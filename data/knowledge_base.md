# TÀI LIỆU NỘI BỘ & CHÍNH SÁCH DOANH NGHIỆP (KNOWLEDGE BASE)

## 1. Chính sách Bảo hành và Đổi trả (Warranty & Refund Policy)
- **Thời hạn đổi trả 1-đổi-1:** Trong vòng **15 ngày đầu tiên** kể từ ngày nhận hàng nếu phát sinh lỗi phần cứng từ nhà sản xuất (màn hình sọc, lỗi mainboard, pin sụt quá 20% trong 24h).
- **Điều kiện hoàn tiền 100% (Full Refund):** Khách hàng được hoàn tiền 100% nếu đơn hàng giao trễ quá **7 ngày** so với cam kết ETA hoặc sản phẩm bị móp méo, vỡ nát trong quá trình vận chuyển (cần có video đồng kiểm).
- **Trường hợp từ chối bảo hành:** Sản phẩm bị vào nước, rơi vỡ do lỗi người dùng, tự ý tháo mở tem niêm phong hoặc can thiệp phần mềm trái phép.

## 2. Chương trình Phân hạng Thành viên & Ưu đãi VIP (Loyalty Tiers)
- **Hạng Kim Cương (Diamond VIP - Cụm K-Means #0):** Chi tiêu tích lũy (Monetary) từ **$1,500 trở lên** và mua tối thiểu **10 đơn/năm**. Quyền lợi: Miễn phí giao hàng hỏa tốc 2h, hoàn tiền 8% mọi đơn hàng, có chuyên viên hỗ trợ riêng 24/7.
- **Hạng Vàng (Gold Member - Cụm K-Means #1):** Chi tiêu tích lũy từ **$500 đến dưới $1,500**. Quyền lợi: Miễn phí giao hàng tiêu chuẩn, tặng voucher giảm 15% (tối đa $50) vào tháng sinh nhật.
- **Nhóm Nguy cơ Rời bỏ cao (High Churn Risk - Cụm K-Means #2):** Khách hàng đã quá **60 ngày chưa quay lại mua sắm** (`recency > 60`) hoặc có tỷ lệ hủy đơn `cancel_rate > 25%`. Hệ thống AI tự động kích hoạt gói **Win-back Voucher giảm 25%** để giữ chân.

## 3. Quy trình Xử lý Đơn hàng Bất thường & Gian lận (Fraud & Anomaly Protocol)
- Các đơn hàng bị thuật toán **DBSCAN** gắn nhãn `Noise = -1` hoặc **SVM** cảnh báo gian lận (giá trị đơn cao gấp 5 lần trung bình lịch sử, địa chỉ giao hàng lệch tâm bất thường) sẽ bị tạm giữ **24 giờ** để bộ phận Risk Management xác minh qua cuộc gọi video (eKYC).
