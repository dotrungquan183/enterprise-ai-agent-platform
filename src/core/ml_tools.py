import os
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

class ClassicalMLToolbox:
    def __init__(self):
        self.model_ready_flag = os.path.join(MODEL_DIR, "rf_churn.pkl")
        if not os.path.exists(self.model_ready_flag):
            self._bootstrap_and_train_models()
        self._load_models()

    def _bootstrap_and_train_models(self):
        print("[ML Toolbox] Đang khởi tạo dữ liệu & huấn luyện nhanh các mô hình ML phục vụ Chat AI...")
        np.random.seed(42)
        n = 2000

        cust_ids = [f"CUST_{i:03d}" for i in range(1, n + 1)]
        recency = np.random.randint(1, 150, size=n)
        frequency = np.random.randint(1, 25, size=n)
        monetary = np.round(frequency * np.random.uniform(35, 120, size=n), 2)
        cancel_rate = np.round(np.random.beta(1.5, 8, size=n), 3)

        # Cố định 3 khách hàng mẫu để dễ test trên khung chat
        recency[0], frequency[0], monetary[0], cancel_rate[0] = 95, 2, 110.0, 0.40   # CUST_001: Nguy cơ rời bỏ cao
        recency[1], frequency[1], monetary[1], cancel_rate[1] = 5, 18, 2150.0, 0.02  # CUST_002: Khách VIP Kim Cương
        recency[2], frequency[2], monetary[2], cancel_rate[2] = 30, 6, 480.0, 0.10   # CUST_003: Khách Vàng ổn định

        clv_target = np.round(monetary * 1.3 + frequency * 20 - recency * 1.5, 2)
        churn_target = ((recency > 65) | (cancel_rate > 0.28)).astype(int)

        self.customer_df = pd.DataFrame({
            "customer_id": cust_ids,
            "recency": recency,
            "frequency": frequency,
            "monetary": monetary,
            "cancel_rate": cancel_rate,
            "target_clv": clv_target,
            "target_churn": churn_target
        })
        self.customer_df.to_parquet(os.path.join(MODEL_DIR, "customers_db.parquet"), index=False)

        X = self.customer_df[["recency", "frequency", "monetary", "cancel_rate"]].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        pca = PCA(n_components=2, random_state=42)
        Z_pca = pca.fit_transform(X_scaled)
        kmeans = KMeans(n_clusters=3, n_init=10, random_state=42).fit(Z_pca)
        dbscan = DBSCAN(eps=0.8, min_samples=10).fit(X_scaled)

        ridge_clv = Ridge(alpha=1.0).fit(X_scaled, clv_target)
        log_churn = LogisticRegression().fit(X_scaled, churn_target)
        rf_churn = RandomForestClassifier(n_estimators=80, max_depth=6, random_state=42).fit(X, churn_target)

        baskets = (
            [["Laptop", "Mouse", "Keyboard", "USB_Hub"]] * 120 +
            [["Laptop", "Mouse", "Monitor"]] * 80 +
            [["Smartphone", "Phone_Case", "Charger", "PowerBank"]] * 150 +
            [["Smartphone", "Earphones", "Charger"]] * 90 +
            [["Book_ML", "Book_Math", "Notebook"]] * 110
        )
        te = TransactionEncoder()
        basket_mat = pd.DataFrame(te.fit_transform(baskets), columns=te.columns_)
        freq_items = fpgrowth(basket_mat, min_support=0.05, use_colnames=True)
        rules = association_rules(freq_items, metric="confidence", min_threshold=0.5)
        rules["antecedents"] = rules["antecedents"].apply(lambda s: list(s))
        rules["consequents"] = rules["consequents"].apply(lambda s: list(s))
        rules.to_parquet(os.path.join(MODEL_DIR, "fpgrowth_rules.parquet"), index=False)

        texts = [
            "sản phẩm tuyệt vời giao nhanh rất hài lòng chất lượng tốt",
            "máy chạy êm pin khỏe đóng gói đẹp đáng tiền",
            "hàng lỗi hỏng giao chậm thất vọng muốn hoàn tiền",
            "kém chất lượng lừa đảo móp méo không lên nguồn"
        ] * 50
        labels = [1, 1, 0, 0] * 50
        vec = TfidfVectorizer()
        X_txt = vec.fit_transform(texts)
        nb = MultinomialNB().fit(X_txt, labels)

        joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
        joblib.dump(pca, os.path.join(MODEL_DIR, "pca.pkl"))
        joblib.dump(kmeans, os.path.join(MODEL_DIR, "kmeans.pkl"))
        joblib.dump(ridge_clv, os.path.join(MODEL_DIR, "ridge_clv.pkl"))
        joblib.dump(log_churn, os.path.join(MODEL_DIR, "log_churn.pkl"))
        joblib.dump(rf_churn, os.path.join(MODEL_DIR, "rf_churn.pkl"))
        joblib.dump((vec, nb), os.path.join(MODEL_DIR, "nb_sentiment.pkl"))
        print("[ML Toolbox] Đã huấn luyện xong toàn bộ mô hình ML!")

    def _load_models(self):
        self.customer_df = pd.read_parquet(os.path.join(MODEL_DIR, "customers_db.parquet"))
        self.rules_df = pd.read_parquet(os.path.join(MODEL_DIR, "fpgrowth_rules.parquet"))
        self.scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        self.pca = joblib.load(os.path.join(MODEL_DIR, "pca.pkl"))
        self.kmeans = joblib.load(os.path.join(MODEL_DIR, "kmeans.pkl"))
        self.ridge_clv = joblib.load(os.path.join(MODEL_DIR, "ridge_clv.pkl"))
        self.log_churn = joblib.load(os.path.join(MODEL_DIR, "log_churn.pkl"))
        self.rf_churn = joblib.load(os.path.join(MODEL_DIR, "rf_churn.pkl"))
        self.vec, self.nb = joblib.load(os.path.join(MODEL_DIR, "nb_sentiment.pkl"))

    def analyze_customer_tool(self, customer_id: str) -> dict:
        customer_id = customer_id.upper().strip()
        row = self.customer_df[self.customer_df["customer_id"] == customer_id]
        if row.empty:
            return {"error": f"Không tìm thấy mã {customer_id} (Hãy thử CUST_001, CUST_002, CUST_003)."}

        r = row.iloc[0]
        feat = np.array([[r["recency"], r["frequency"], r["monetary"], r["cancel_rate"]]])
        feat_scaled = self.scaler.transform(feat)
        z_pca = self.pca.transform(feat_scaled)

        seg_id = int(self.kmeans.predict(z_pca)[0])
        clv_pred = float(self.ridge_clv.predict(feat_scaled)[0])
        churn_prob_rf = float(self.rf_churn.predict_proba(feat)[0, 1])
        churn_prob_log = float(self.log_churn.predict_proba(feat_scaled)[0, 1])

        return {
            "tool_used": "ML_Customer_360_Profiler (PCA + K-Means + Ridge + Logistic + RandomForest)",
            "customer_id": customer_id,
            "raw_metrics": {
                "recency_days": int(r["recency"]),
                "frequency_orders": int(r["frequency"]),
                "monetary_usd": float(r["monetary"]),
                "cancel_rate": float(r["cancel_rate"])
            },
            "ml_predictions": {
                "kmeans_segment": f"Cluster #{seg_id}",
                "pca_coordinates": [round(float(z_pca[0, 0]), 3), round(float(z_pca[0, 1]), 3)],
                "predicted_12m_clv_usd": round(clv_pred, 2),
                "churn_probability_random_forest": f"{churn_prob_rf*100:.1f}%",
                "churn_probability_logistic": f"{churn_prob_log*100:.1f}%",
                "churn_risk_label": "NGUY CƠ CAO (HIGH RISK)" if churn_prob_rf >= 0.5 else "AN TOÀN (LOW RISK)"
            }
        }

    def recommend_cross_sell_tool(self, item_name: str) -> dict:
        matched = self.rules_df[self.rules_df["antecedents"].apply(
            lambda items: any(item_name.lower() in i.lower() for i in items)
        )].sort_values(by="lift", ascending=False)

        if matched.empty:
            return {
                "tool_used": "FPGrowth_Basket_Recommender",
                "queried_item": item_name,
                "recommendations": ["Mouse", "Keyboard", "Charger"],
                "note": "Gợi ý mặc định (Hãy thử hỏi về: Laptop, Smartphone, Book_ML)."
            }

        recs = []
        for _, row in matched.head(4).iterrows():
            recs.append({
                "when_buying": list(row["antecedents"]),
                "recommend_buying": list(row["consequents"]),
                "confidence": f"{row['confidence']*100:.1f}%",
                "lift": round(float(row["lift"]), 2)
            })
        return {
            "tool_used": "FPGrowth_Basket_Recommender (Prefix-Tree Association Rules)",
            "queried_item": item_name,
            "top_rules": recs
        }

    def analyze_sentiment_tool(self, text: str) -> dict:
        vec_txt = self.vec.transform([text])
        prob_pos = float(self.nb.predict_proba(vec_txt)[0, 1])
        return {
            "tool_used": "Multinomial_Naive_Bayes_NLP",
            "input_text": text,
            "sentiment": "TÍCH CỰC (POSITIVE)" if prob_pos >= 0.5 else "TIÊU CỰC / KHIẾU NẠI (NEGATIVE)",
            "positive_probability": f"{prob_pos*100:.1f}%"
        }
