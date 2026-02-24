import pandas as pd
import numpy as np
import logging
from persist.models import Transaction, ConsumeCategory
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import jieba

logger = logging.getLogger("finmind.analyzer")

class LifestyleAnalyzer:
    def analyze(self, user_id=None, months=6):
        """
        Analyze user lifestyle based on recent transactions using KMeans clustering.
        Features are dynamically generated based on finsight.consume_category.
        """
        logger.info(f"Starting Lifestyle Analysis. User: {user_id}, Months: {months}")
        
        # 0. Load Categories Map
        # User instruction: transaction.consume_code -> consume_category.id
        category_map = {}
        try:
            cats = ConsumeCategory.objects.all()
            for c in cats:
                # Map ID to Name for readable features
                category_map[str(c.id)] = c.name
            logger.info(f"Loaded {len(category_map)} categories from database.")
        except Exception as e:
            logger.error(f"Failed to load categories: {e}")
            pass

        # 1. Fetch real data
        qs = Transaction.objects.exclude(deleted=1)
        # Optional: filter by user if needed
        # qs = qs.filter(...) 
        logger.info(f"Found {qs.count()} total active transactions.")
        
        # Convert to list of dicts for DataFrame

        data = []
        for t in qs:
            amt = 0
            if t.income_money:
                amt = float(t.income_money)
            elif t.balance_money:
                amt = float(t.balance_money)
            # Use absolute value for spending analysis
            amt = abs(amt)
            
            # Resolve category name
            # consume_code links to category.id
            cat_id = str(t.consume_code or "")
            cat_name = category_map.get(cat_id)
            
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
                "category_id": cat_id
            })
            
        if not data:
            return {"error": "No transactions found"}
            
        df = pd.DataFrame(data)
        
        # 2. Feature Engineering (Dynamic Categories)
        logger.info("Starting feature engineering...")
        # Get list of all unique categories in the dataset
        unique_cats = df['category_name'].unique()
        logger.info(f"Unique categories found in transactions: {len(unique_cats)}")

        
        def extract_features(row):
            features = {'amount': row['amount']}
            # One-hot like encoding for the category of this transaction
            # Since we are clustering transactions, each row is one transaction, so only one category is 1, others 0
            # This helps group similar transactions together
            current_cat = row['category_name']
            
            for c in unique_cats:
                features[f'cat_{c}'] = 1 if c == current_cat else 0
                
            return pd.Series(features)

        df_features = df.apply(extract_features, axis=1)
        
        # 3. KMeans Clustering
        logger.info(f"Clustering with {len(df_features)} samples...")
        # Select features for clustering

        feature_cols = [c for c in df_features.columns]
        X = df_features[feature_cols]
        
        # Handle empty or too few data points
        if len(X) < 3:
             return {"error": "Not enough data for clustering (need at least 3 transactions)"}

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Default to 3 clusters, or less if data is small
        n_clusters = min(3, len(X))
        logger.info(f"Using {n_clusters} clusters.")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)

        df['lifestyle_label'] = kmeans.fit_predict(X_scaled)
        
        # 4. Generate Report
        report = {}
        cluster_summaries = []
        
        # Helper to find dominant categories in a cluster
        for label in sorted(df['lifestyle_label'].unique()):
            subset = df[df['lifestyle_label'] == label]
            avg_amount = subset['amount'].mean()
            total_count = len(subset)
            
            # Calculate distribution of categories in this cluster
            cat_counts = subset['category_name'].value_counts()
            if not cat_counts.empty:
                top_cat = cat_counts.index[0]
                top_cat_count = cat_counts.iloc[0]
                ratio = top_cat_count / total_count
                
                # Naming the vibe
                if ratio > 0.5:
                    vibe = f"�️ {top_cat} 消费"
                else:
                    vibe = "🧩 混合消费模式"
                    
                # Refine vibe based on amount
                if avg_amount > 1000:
                    vibe += " (高额)"
            else:
                vibe = "❓ 未知模式"

            # Create detailed description
            top_3 = cat_counts.head(3).index.tolist()
            desc_str = ", ".join(top_3)
            
            report[int(label)] = {
                'vibe': vibe,
                'avg_spend': round(avg_amount, 2),
                'total_transactions': total_count,
                'top_categories': top_3
            }
            logger.info(f"Cluster {label}: {vibe}, Count={total_count}, AvgSpend={avg_amount:.2f}")
            cluster_summaries.append(report[int(label)])

            
        # 5. Current Month / Recent Diagnosis
        if not df.empty:
            last_txn = df.iloc[-1]
            today_label = int(last_txn['lifestyle_label'])
            current_vibe_info = report.get(today_label, {})
            current_vibe = current_vibe_info.get('vibe', '未知')
            
            # Generate tips based on global stats
            # e.g., if highest spending category is X
            total_spend_by_cat = df.groupby('category_name')['amount'].sum().sort_values(ascending=False)
            top_spend_cat = total_spend_by_cat.index[0] if not total_spend_by_cat.empty else "None"
            
            tips = f"您最近在【{top_spend_cat}】方面花费最多。保持记录，继续优化！"
            
            result = {
                "diagnosis": {
                    "vibe": current_vibe,
                    "avg_spend": current_vibe_info.get('avg_spend', 0),
                    "total_txns": current_vibe_info.get('total_transactions', 0)
                },
                "tips": tips,
                "clusters": cluster_summaries,
                "total_analyzed": len(df)
            }
            logger.info("Analysis complete.")
            return result
            
        logger.warning("No data found for analysis.")
        return {"error": "Analysis failed"}

