import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from persist.models import Transaction, ConsumeCategory
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger("finmind.analyzer")

class LifestyleAnalyzer:
    TARGET_PARENTS = ['FIXED', 'LIVING', 'SHOPPING', 'TRANSPORT', 'EDU', 'ENT', 'SOCIAL', 'A10001', 'B10001', 'C10001', 'D10001', 'J10001']

    def analyze(self, user_id=None, months=6):
        """
        Main entry point for lifestyle analysis.
        Orchestrates data preparation, fixed expense detection, clustering, and prediction.
        """
        logger.info(f"Starting Enhanced Lifestyle Analysis. User: {user_id}, Months: {months}")
        
        # 1. Prepare Data (with enhanced features)
        df = self.prepare_data(user_id, months)
        
        if df is None or df.empty:
            logger.warning("No data found for analysis.")
            return {"error": "Analysis failed: No data found"}
            
        # 2. Run Algorithm (Clustering + Prediction + Fixed Expense Detection)
        return self.run_clustering_algorithm(df, months)

    def prepare_data(self, user_id=None, months=6):
        """
        Fetches data and performs enhanced feature engineering (Time, Text).
        """
        # Load Maps
        category_map, parent_map, parent_names, category_types = self._load_category_metadata()
        
        from django.utils import timezone
        
        # Fetch Transactions
        qs = Transaction.objects.exclude(deleted=1)
        
        if user_id:
            qs = qs.filter(createuser=user_id)
            
        if months:
            start_date = timezone.now() - timedelta(days=months*30)
            qs = qs.filter(transaction_date__gte=start_date)
            
        logger.info(f"Found {qs.count()} total active transactions.")
        
        if not qs.exists():
            return None

        # Process Data
        data = []
        excluded_parents = ['INC', 'ASSET', 'LIABILITY', 'INVEST', 'REIMB', 'FP', 'J10001']
        
        for t in qs:
            # Resolve category info
            cat_id = str(t.consume_code or "")
            cat_name = category_map.get(cat_id)
            
            # Resolve parent category
            parent_id = parent_map.get(cat_id)
            
            # If the category itself is one of the target parents (top-level transaction)
            if cat_id in self.TARGET_PARENTS:
                parent_id = cat_id
            
            # Check exclusions (Income, Transfers, Investments, Debt Repayments)
            if parent_id in excluded_parents or cat_id in excluded_parents:
                continue
                
            parent_name = parent_names.get(parent_id) if parent_id else "Other"
            if not parent_name:
                parent_name = "Other"
            
            # Skip non-expense transactions (Income, Transfer, Adjustment, etc.)
            cat_type = category_types.get(cat_id, "expense")
            if cat_type != "expense":
                # Special case: SOCIAL is marked as adjustment but is a lifestyle expense
                if parent_id == 'SOCIAL':
                    pass
                else:
                    continue
            
            # Safeguard: Skip transactions with income_money > 0 (likely income/refund)
            if t.income_money and float(t.income_money) > 0:
                continue
                
            amt = 0
            if t.income_money:
                amt = float(t.income_money)
            elif t.balance_money:
                amt = float(t.balance_money)
            
            # Use absolute value for spending analysis
            amt = abs(amt)
            
            # Fallback if lookup fails
            if not cat_name:
                cat_name = t.consume_name or "Uncategorized"
                
            desc = (t.transaction_desc or "")
            
            data.append({
                "id": t.id,
                "date": t.transaction_date,
                "amount": amt,
                "desc": desc,
                "category_name": cat_name,
                "category_id": cat_id,
                "parent_name": parent_name,
                "parent_id": parent_id,
                "merchant": getattr(t, "opponent_name", "") or getattr(t, "bank_card_name", "") or ""
            })
            
        df = pd.DataFrame(data)
        
        if df.empty:
            return None
            
        # --- Enhanced Feature Engineering ---
        logger.info("Enhanced Feature Engineering: Adding time features...")
        
        # Ensure date is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # 1. Time Features
        df['hour'] = df['date'].dt.hour
        df['is_weekend'] = df['date'].dt.dayofweek >= 5
        
        # 2. Consumption Rhythm (Time Diff)
        # Sort by date to calculate interval
        df = df.sort_values('date')
        df['time_diff_hours'] = df['date'].diff().dt.total_seconds() / 3600.0
        df['time_diff_hours'] = df['time_diff_hours'].fillna(0) # First txn has no previous
        
        # Time Period Logic
        def get_time_period(hour):
            if 5 <= hour < 9: return "Breakfast"
            elif 11 <= hour < 14: return "Lunch"
            elif 17 <= hour < 21: return "Dinner"
            elif 21 <= hour or hour < 5: return "NightLife"
            else: return "Work/Other"
            
        df['time_period'] = df['hour'].apply(get_time_period)
        
        return df

    def _load_category_metadata(self):
        """
        Helper to load category mappings from DB.
        Returns: (category_map, parent_map, parent_names, category_types)
        """
        category_map = {}
        parent_map = {} # child_id -> parent_id
        parent_names = {} # parent_id -> parent_name
        category_types = {} # id -> txn_types
        
        try:
            cats = ConsumeCategory.objects.all()
            for c in cats:
                category_map[str(c.id)] = c.name
                category_types[str(c.id)] = c.txn_types
                if c.parentId:
                    parent_map[str(c.id)] = str(c.parentId)
                else:
                    # It is a parent (top-level) category
                    parent_names[str(c.id)] = c.name
                
                # Check if this category is a target parent or its ID is in target parents
                if str(c.id) in self.TARGET_PARENTS:
                    parent_names[str(c.id)] = c.name
                    
            logger.info(f"Loaded {len(category_map)} categories from database.")
        except Exception as e:
            logger.error(f"Failed to load categories: {e}")
            
        return category_map, parent_map, parent_names, category_types

    def identify_fixed_expenses(self, df):
        """
        Identifies fixed expenses using statistical heuristics (Low Variance + Regularity).
        Adds 'predicted_fixed' column (1 for fixed, 0 for variable).
        """
        logger.info("Identifying fixed expenses...")
        
        # Heuristic: Group by category, check Amount CV (Coef of Variation) & Date Regularity
        # Fixed expenses usually have same amount (CV ~ 0) and occur regularly (Day Std ~ 0).
        
        # 0. Pre-calc Day of Month
        df['day'] = df['date'].dt.day
        
        # 1. Calculate stats per category
        # Aggregation: Amount (count, mean, std), Day (std)
        cat_stats = df.groupby('category_name').agg({
            'amount': ['count', 'mean', 'std'],
            'day': ['std']
        })
        
        # Flatten MultiIndex columns
        cat_stats.columns = ['count', 'amount_mean', 'amount_std', 'day_std']
        cat_stats = cat_stats.reset_index()
        
        # Fill NA for single transactions (std is NaN)
        cat_stats['amount_std'] = cat_stats['amount_std'].fillna(0)
        cat_stats['day_std'] = cat_stats['day_std'].fillna(0)
        
        # Calculate CV
        cat_stats['cv'] = cat_stats.apply(lambda x: x['amount_std'] / x['amount_mean'] if x['amount_mean'] > 0 else 0, axis=1)
        
        # 2. Define Rules for "Fixed"
        # Rule 1: Count >= 2 (must recur) AND CV < 0.15 (very stable amount, e.g. Netflix, Rent)
        # Rule 2: Count >= 2 AND Day Std < 3.0 (very regular timing, e.g. Utilities, Credit Card Bill)
        
        fixed_cats_amount = cat_stats[
            (cat_stats['count'] >= 2) & 
            (cat_stats['cv'] < 0.15) 
        ]['category_name'].tolist()
        
        fixed_cats_time = cat_stats[
            (cat_stats['count'] >= 2) & 
            (cat_stats['day_std'] < 3.0)
        ]['category_name'].tolist()
        
        fixed_cats = list(set(fixed_cats_amount + fixed_cats_time))
        
        # Also include "FIXED" parent transactions if any
        fixed_parent_txns = df[df['parent_name'] == 'FIXED']['category_name'].unique().tolist()
        fixed_cats = list(set(fixed_cats + fixed_parent_txns))
        
        logger.info(f"Identified {len(fixed_cats)} fixed expense categories: {fixed_cats}")
        
        df['predicted_fixed'] = df['category_name'].apply(lambda x: 1 if x in fixed_cats else 0)
        non_essential_parents = ['SHOPPING', 'ENT', 'SOCIAL', '购物消费', '数码电器', 'C10001', 'D10001']
        df['is_non_essential'] = df['parent_name'].isin(non_essential_parents).astype(int)
        
        return df

    def predict_next_month_budget(self, df):
        """
        Predicts next month's total budget using Linear Regression on monthly totals.
        """
        try:
            # 1. Aggregate by Month
            # Use period 'ME' (Month End) to group as 'M' is deprecated
            monthly_df = df.set_index('date').resample('ME')['amount'].sum().reset_index()
            
            if len(monthly_df) < 2:
                return {"status": "insufficient_data", "msg": "Need at least 2 months of data"}
            
            # 2. Prepare X (Ordinal Date) and y (Amount)
            monthly_df['month_ordinal'] = monthly_df['date'].map(datetime.toordinal)
            
            X = monthly_df[['month_ordinal']]
            y = monthly_df['amount']
            
            # 3. Fit Model
            model = LinearRegression()
            model.fit(X, y)
            
            # 4. Predict Next Month
            last_date = monthly_df['date'].iloc[-1]
            next_month_date = last_date + timedelta(days=30) # Approx
            
            # Use DataFrame with same feature name to avoid warning
            next_month_df = pd.DataFrame({'month_ordinal': [next_month_date.toordinal()]})
            
            pred_amount = model.predict(next_month_df)[0]
            
            # Calculate Trend (Percentage change from last month)
            last_month_actual = monthly_df['amount'].iloc[-1]
            diff_ratio = (pred_amount - last_month_actual) / last_month_actual if last_month_actual > 0 else 0
            
            trend = "预计持平"
            if diff_ratio > 0.05:
                trend = f"预计增加 {int(diff_ratio * 100)}%"
            elif diff_ratio < -0.05:
                trend = f"预计减少 {int(abs(diff_ratio) * 100)}%"
            
            return {
                "next_month_amount": max(0, round(pred_amount, 2)),
                "trend": trend,
                "confidence": "Medium" 
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {"error": str(e)}

    def run_clustering_algorithm(self, df, months=6):
        """
        Performs Fixed Expense Detection, Feature Engineering, Clustering, and Prediction.
        """
        # 1. Identify Fixed Expenses (New Step)
        df = self.identify_fixed_expenses(df)
        
        logger.info("Starting feature engineering for clustering...")
        
        # 2. Feature Engineering for Clustering
        # We use One-Hot Encoding for categorical features and standard scaling
        
        # Reset index to ensure alignment
        df = df.sort_values('date').reset_index(drop=True)
        
        # Select features
        # Base numerical features
        feature_cols = ['amount', 'hour', 'is_weekend', 'time_diff_hours']
        
        # One-Hot Encoding for Parent Categories
        parent_dummies = pd.get_dummies(df['parent_name'], prefix='parent')
        df_encoded = pd.concat([df, parent_dummies], axis=1)
        
        # One-Hot Encoding for Time Period
        period_dummies = pd.get_dummies(df['time_period'], prefix='period')
        df_encoded = pd.concat([df_encoded, period_dummies], axis=1)
        
        # Text Semantic Feature (TF-IDF)
        tfidf_cols = []
        try:
            # Combine desc and category for text analysis
            # Ensure text is string and fillna
            text_data = (df['desc'].fillna('') + " " + df['category_name'].fillna('')).astype(str)
            
            # Limit features to keep dimensions reasonable
            # Use simple token pattern to include Chinese/English words
            tfidf = TfidfVectorizer(max_features=5, stop_words='english')
            tfidf_matrix = tfidf.fit_transform(text_data)
            
            # Create DataFrame for TF-IDF features
            tfidf_df = pd.DataFrame(
                tfidf_matrix.toarray(), 
                columns=[f'tfidf_{i}' for i in range(tfidf_matrix.shape[1])]
            )
            
            df_encoded = pd.concat([df_encoded, tfidf_df], axis=1)
            tfidf_cols = list(tfidf_df.columns)
            logger.info(f"Added {len(tfidf_cols)} TF-IDF text features.")
            
        except Exception as e:
            logger.warning(f"TF-IDF feature engineering failed: {e}")

        # Collect all feature columns
        train_cols = ['amount', 'hour', 'is_weekend', 'time_diff_hours'] + \
                     list(parent_dummies.columns) + \
                     list(period_dummies.columns) + \
                     tfidf_cols
                     
        X = df_encoded[train_cols].fillna(0) # Ensure no NaN
        
        if len(X) < 3:
             return {"error": "Not enough data for clustering (need at least 3 transactions)"}

        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 3. KMeans Clustering
        n_clusters = min(5, len(X)) # Increased max clusters to 5 for finer granularity
        logger.info(f"Using {n_clusters} clusters.")
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['lifestyle_label'] = kmeans.fit_predict(X_scaled)
        
        # 4. Generate Enhanced Report
        return self._generate_report(df, n_clusters, months)

    def _generate_report(self, df, n_clusters, months=6):
        """
        Generates the final diagnosis report including Fixed Expenses and Predictions.
        """
        # Handle 'All Time' (months=0 or None) by calculating actual duration
        if not months or months <= 0:
            if not df.empty:
                min_date = df['date'].min()
                max_date = df['date'].max()
                days = (max_date - min_date).days
                months = max(1, round(days / 30.0))
            else:
                months = 1

        report = {}
        cluster_summaries = []
        for label in sorted(df['lifestyle_label'].unique()):
            subset = df[df['lifestyle_label'] == label]
            avg_amount = subset['amount'].mean()
            total_count = len(subset)
            top_parent = subset['parent_name'].mode()[0] if not subset['parent_name'].empty else "Unknown"
            top_period = subset['time_period'].mode()[0] if not subset['time_period'].empty else "Anytime"
            vibe = f"{top_parent} ({top_period})"
            if top_period == "NightLife":
                vibe = "🦉 夜猫子消费"
            elif top_period == "Breakfast":
                vibe = "🥣 早起鸟"
            elif top_parent == "SHOPPING" and avg_amount > 500:
                vibe = "🛍️ 剁手一族"
            elif top_parent == "FIXED":
                vibe = "💸 固定开销"
            elif top_parent == "ENT":
                vibe = "🎮 享乐主义"
            cluster_info = {
                "vibe": vibe,
                "avg_spend": round(avg_amount, 2),
                "total_transactions": total_count,
                "top_categories": subset["category_name"].value_counts().head(3).index.tolist()
            }
            report[int(label)] = cluster_info
            cluster_summaries.append(cluster_info)
            logger.info(f"Cluster {label}: {vibe}, Count={total_count}")

        fixed_df = df[df["predicted_fixed"] == 1]
        fixed_ratio = round(len(fixed_df) / len(df), 2) if len(df) > 0 else 0
        estimated_monthly_fixed = float(fixed_df["amount"].sum() / months) if len(fixed_df) > 0 else 0.0
        
        fixed_details = []
        if not fixed_df.empty:
            f_stats = fixed_df.groupby("category_name").agg({
                "amount": "mean",
                "day": "mean"
            }).reset_index()
            f_stats = f_stats.sort_values("amount", ascending=False).head(5)
            for _, row in f_stats.iterrows():
                fixed_details.append({
                    "name": row["category_name"],
                    "amount": round(row["amount"], 2),
                    "day": int(round(row["day"]))
                })

        fixed_analysis = {
            "total_fixed_count": int(len(fixed_df)),
            "fixed_categories": fixed_df["category_name"].unique().tolist()[:10],
            "estimated_monthly_fixed": estimated_monthly_fixed,
            "fixed_ratio": fixed_ratio,
            "details": fixed_details
        }

        budget_pred = self.predict_next_month_budget(df)

        if not df.empty:
            last_txn = df.iloc[-1]
            current_cluster = int(last_txn["lifestyle_label"])
            current_vibe = report.get(current_cluster, {}).get("vibe", "未知")
        else:
            current_vibe = "无数据"

        overall_avg = round(df["amount"].mean(), 2) if len(df) > 0 else 0.0

        tips = "建议关注固定支出占比，并为下个月的预算做好准备。"
        if fixed_analysis["fixed_ratio"] > 0.6:
            tips = "您的固定支出占比很高，建议检查是否有可优化的订阅或合约。"
        elif str(budget_pred.get("trend", "")).startswith("预计增加"):
            tips = "检测到消费呈上升趋势，建议下个月适当控制非必要开支。"

        df_ts = df.copy()
        df_ts["date_only"] = df_ts["date"].dt.date
        ts_points = []
        for d, g in df_ts.groupby("date_only"):
            modes_amount = g.groupby("time_period")["amount"].sum().to_dict()
            ts_points.append({
                "date": d.isoformat(),
                "total": float(g["amount"].sum()),
                "non_essential": float(g.loc[g["is_non_essential"] == 1, "amount"].sum()),
                "fixed_expense": float(g.loc[g["predicted_fixed"] == 1, "amount"].sum()),
                "modes": {k: float(v) for k, v in modes_amount.items()}
            })
        ts_points = sorted(ts_points, key=lambda x: x["date"])
        timeseries = {
            "granularity": "day",
            "points": ts_points
        }

        total_amount = float(df["amount"].sum()) if len(df) > 0 else 0.0
        total_count = int(len(df))
        total_amount_safe = total_amount if total_amount > 0 else 1.0
        total_count_safe = total_count if total_count > 0 else 1
        label_map = {
            "NightLife": "夜猫子消费",
            "Breakfast": "早餐",
            "Lunch": "午餐",
            "Dinner": "晚餐",
            "Work/Other": "日常生活"
        }
        radar = []
        mode_stats = {}
        for period, g in df.groupby("time_period"):
            amt = float(g["amount"].sum())
            cnt = int(len(g))
            amount_ratio = round(amt / total_amount_safe, 4)
            count_ratio = round(cnt / total_count_safe, 4)
            label = label_map.get(period, period)
            radar.append({
                "mode": period,
                "label": label,
                "amount_ratio": amount_ratio,
                "count_ratio": count_ratio
            })
            mode_stats[period] = {
                "amount": amt,
                "count": cnt,
                "amount_ratio": amount_ratio,
                "count_ratio": count_ratio
            }

        modes = []
        for period, g in df.groupby("time_period"):
            stats = mode_stats.get(period) or {}
            
            # Use ALL data for this mode, but sort by date descending to get "Recent"
            # Instead of a hard 7-day cutoff from global max date
            mode_recent = g.sort_values("date", ascending=False).head(20) # Top 20 recent
            
            label = label_map.get(period, period)
            top_merchants = []
            scenes = []
            time_buckets = []
            recent_txns = []
            
            if not mode_recent.empty:
                merchant_series = mode_recent["merchant"].fillna("").replace("", np.nan).dropna()
                if not merchant_series.empty:
                    merchant_stats = mode_recent.groupby("merchant")["amount"].sum().sort_values(ascending=False).head(3)
                    top_merchants = [{
                        "name": str(name),
                        "total": float(val)
                    } for name, val in merchant_stats.items()]
                
                # Use the full group 'g' for scene distribution to be more representative? 
                # Or just recent? Let's use recent to reflect "current" habits.
                scene_series = mode_recent["category_name"].value_counts(normalize=True).head(3)
                scenes = [{
                    "name": str(name),
                    "ratio": float(round(ratio, 4))
                } for name, ratio in scene_series.items()]
                
                def bucket(h):
                    if period == "NightLife":
                        if 22 <= h < 24:
                            return "22:00-24:00"
                        if 0 <= h < 2:
                            return "00:00-02:00"
                        return "其他夜间"
                    return "全天"
                
                mode_recent_copy = mode_recent.copy()
                mode_recent_copy["time_bucket"] = mode_recent_copy["hour"].apply(bucket)
                tb_series = mode_recent_copy["time_bucket"].value_counts(normalize=True)
                time_buckets = [{
                    "label": str(name),
                    "ratio": float(round(ratio, 4))
                } for name, ratio in tb_series.items()]
                
                # Transaction list (already sorted)
                for _, row in mode_recent.iterrows():
                    dval = row["date"]
                    dstr = dval.isoformat() if not pd.isna(dval) else None
                    recent_txns.append({
                        "id": row["id"],
                        "date": dstr,
                        "amount": float(row["amount"]),
                        "category": str(row["category_name"]) if pd.notna(row["category_name"]) else "Uncategorized",
                        "parent": str(row["parent_name"]) if pd.notna(row["parent_name"]) else "Other",
                        "merchant": str(row["merchant"]) if pd.notna(row["merchant"]) else "",
                        "desc": str(row["desc"]) if pd.notna(row["desc"]) else ""
                    })
                    
            modes.append({
                "key": period,
                "label": label,
                "total_amount": float(stats.get("amount", 0.0)),
                "txn_count": int(stats.get("count", 0)),
                "amount_ratio": float(stats.get("amount_ratio", 0.0)),
                "count_ratio": float(stats.get("count_ratio", 0.0)),
                "recent_details": {  # Renamed from recent_7d to generic recent_details
                    "top_merchants": top_merchants,
                    "scenes": scenes,
                    "time_buckets": time_buckets,
                    "transactions": recent_txns
                }
            })

        recommendations = []
        night = mode_stats.get("NightLife")
        if night and night.get("amount_ratio", 0) > 0.2:
            recommendations.append("夜猫子消费占比较高，特别是深夜时段，建议为 23:00 后的打车和外卖设置额外确认步骤。")
        work = mode_stats.get("Work/Other")
        if work and work.get("count", 0) > 0:
            work_df = df[df["time_period"] == "Work/Other"]
            high_work = work_df[work_df["amount"] > 500]
            if len(high_work) >= 5:
                recommendations.append("日常工作相关的大额消费较多，建议为设备采购等支出建立简单审批或复盘流程。")
        lunch = mode_stats.get("Lunch")
        if lunch and lunch.get("count_ratio", 0) > 0.1:
            recommendations.append("午餐消费频次较高，可以尝试设置每周餐饮预算，例如每周预存一笔固定午餐额度。")
        if not recommendations:
            recommendations.append("整体消费结构较为平衡，可以继续保持现有节奏，同时定期复盘固定支出和夜间消费。")

        result = {
            "diagnosis": {
                "vibe": current_vibe,
                "avg_spend": overall_avg,
                "total_txns": len(df)
            },
            "tips": tips,
            "clusters": cluster_summaries,
            "fixed_expense_analysis": fixed_analysis,
            "budget_prediction": budget_pred,
            "timeseries": timeseries,
            "radar": radar,
            "modes": modes,
            "recommendations": recommendations,
            "total_analyzed": len(df)
        }
        
        logger.info("Enhanced Analysis complete.")
        return result
