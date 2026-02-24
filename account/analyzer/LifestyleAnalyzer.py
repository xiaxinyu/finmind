import pandas as pd
import numpy as np
import logging
from persist.models import Transaction, ConsumeCategory
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import jieba

logger = logging.getLogger("finmind.analyzer")

class LifestyleAnalyzer:
    TARGET_PARENTS = ['FIXED', 'LIVING', 'SHOPPING', 'TRANSPORT', 'EDU', 'ENT', 'SOCIAL']

    def analyze(self, user_id=None, months=6):
        """
        Main entry point for lifestyle analysis.
        Orchestrates data preparation and clustering algorithm.
        """
        logger.info(f"Starting Lifestyle Analysis. User: {user_id}, Months: {months}")
        
        # 1. Prepare Data
        df = self.prepare_data(user_id, months)
        
        if df is None or df.empty:
            logger.warning("No data found for analysis.")
            return {"error": "Analysis failed: No data found"}
            
        # 2. Run Algorithm
        return self.run_clustering_algorithm(df)

    def prepare_data(self, user_id=None, months=6):
        """
        Fetches data from database and prepares the DataFrame.
        Handles category mapping and hierarchy resolution.
        """
        # Load Maps
        category_map, parent_map, parent_names = self._load_category_metadata()
        
        # Fetch Transactions
        qs = Transaction.objects.exclude(deleted=1)
        # TODO: Implement user_id and months filtering if needed
        # if user_id:
        #     qs = qs.filter(user_id=user_id)
        # if months:
        #     start_date = ...
        #     qs = qs.filter(transaction_date__gte=start_date)
            
        logger.info(f"Found {qs.count()} total active transactions.")
        
        if not qs.exists():
            return None

        # Process Data
        data = []
        for t in qs:
            amt = 0
            if t.income_money:
                amt = float(t.income_money)
            elif t.balance_money:
                amt = float(t.balance_money)
            
            # Use absolute value for spending analysis
            amt = abs(amt)
            
            # Resolve category info
            cat_id = str(t.consume_code or "")
            cat_name = category_map.get(cat_id)
            
            # Resolve parent category
            parent_id = parent_map.get(cat_id)
            
            # If the category itself is one of the target parents (top-level transaction)
            if cat_id in self.TARGET_PARENTS:
                parent_id = cat_id
            
            parent_name = parent_names.get(parent_id) if parent_id else "Other"
            
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
                "parent_id": parent_id
            })
            
        return pd.DataFrame(data)

    def _load_category_metadata(self):
        """
        Helper to load category mappings from DB.
        Returns: (category_map, parent_map, parent_names)
        """
        category_map = {}
        parent_map = {} # child_id -> parent_id
        parent_names = {} # parent_id -> parent_name
        
        try:
            cats = ConsumeCategory.objects.all()
            for c in cats:
                category_map[str(c.id)] = c.name
                if c.parentId:
                    parent_map[str(c.id)] = str(c.parentId)
                
                if str(c.id) in self.TARGET_PARENTS:
                    parent_names[str(c.id)] = c.name
                    
            logger.info(f"Loaded {len(category_map)} categories from database.")
        except Exception as e:
            logger.error(f"Failed to load categories: {e}")
            
        return category_map, parent_map, parent_names

    def run_clustering_algorithm(self, df):
        """
        Performs feature engineering, KMeans clustering, and generates the report.
        """
        logger.info("Starting feature engineering...")
        
        # 1. Feature Engineering
        unique_cats = df['category_name'].unique()
        unique_parents = df['parent_name'].unique()
        logger.info(f"Unique categories: {len(unique_cats)}, Unique parents: {len(unique_parents)}")

        # Closure for feature extraction to capture unique lists
        def extract_features(row):
            features = {'amount': row['amount']}
            
            # Parent Category Features (Higher Weight)
            current_parent = row['parent_name']
            for p in unique_parents:
                features[f'parent_{p}'] = 2 if p == current_parent else 0
            
            # Sub Category Features
            current_cat = row['category_name']
            for c in unique_cats:
                features[f'cat_{c}'] = 1 if c == current_cat else 0
                
            return pd.Series(features)

        df_features = df.apply(extract_features, axis=1)
        
        # 2. KMeans Clustering
        logger.info(f"Clustering with {len(df_features)} samples...")
        
        feature_cols = [c for c in df_features.columns]
        X = df_features[feature_cols]
        
        if len(X) < 3:
             return {"error": "Not enough data for clustering (need at least 3 transactions)"}

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        n_clusters = min(3, len(X))
        logger.info(f"Using {n_clusters} clusters.")
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['lifestyle_label'] = kmeans.fit_predict(X_scaled)
        
        # 3. Generate Report
        return self._generate_report(df, n_clusters)

    def _generate_report(self, df, n_clusters):
        """
        Generates the final diagnosis report from clustered data.
        """
        report = {}
        cluster_summaries = []
        
        # Analyze each cluster
        for label in sorted(df['lifestyle_label'].unique()):
            subset = df[df['lifestyle_label'] == label]
            avg_amount = subset['amount'].mean()
            total_count = len(subset)
            
            parent_counts = subset['parent_name'].value_counts()
            cat_counts = subset['category_name'].value_counts()
            
            vibe = "❓ 未知模式"
            
            if not parent_counts.empty:
                top_parent = parent_counts.index[0]
                top_parent_count = parent_counts.iloc[0]
                parent_ratio = top_parent_count / total_count
                
                # Naming strategy
                if parent_ratio > 0.6:
                    vibe = f"🏷️ {top_parent} 导向"
                    if not cat_counts.empty:
                        top_sub = cat_counts.index[0]
                        if top_sub != top_parent:
                            vibe += f" ({top_sub})"
                else:
                    if not cat_counts.empty and (cat_counts.iloc[0] / total_count > 0.5):
                        vibe = f"🏷️ {cat_counts.index[0]} 专注"
                    else:
                        vibe = "🧩 混合消费模式"
                    
                # Amount qualifiers
                if avg_amount > 2000:
                    vibe += " (高额)"
                elif avg_amount < 100:
                    vibe += " (小额)"

            top_3 = cat_counts.head(3).index.tolist()
            
            cluster_info = {
                'vibe': vibe,
                'avg_spend': round(avg_amount, 2),
                'total_transactions': total_count,
                'top_categories': top_3
            }
            
            report[int(label)] = cluster_info
            cluster_summaries.append(cluster_info)
            logger.info(f"Cluster {label}: {vibe}, Count={total_count}, AvgSpend={avg_amount:.2f}")

        # Current Diagnosis & Tips
        last_txn = df.iloc[-1]
        today_label = int(last_txn['lifestyle_label'])
        current_vibe_info = report.get(today_label, {})
        current_vibe = current_vibe_info.get('vibe', '未知')
        
        total_spend_by_parent = df.groupby('parent_name')['amount'].sum().sort_values(ascending=False)
        top_spend_parent = total_spend_by_parent.index[0] if not total_spend_by_parent.empty else "None"
        
        tips = f"您最近在【{top_spend_parent}】大类方面花费最多。建议检查该类别的具体支出。"
        
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
