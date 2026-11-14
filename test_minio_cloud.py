import os
from minio import Minio
from dotenv import load_dotenv

load_dotenv()

# Lấy thông tin cấu hình từ biến môi trường hoặc Streamlit secrets
endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
access_key = os.getenv("MINIO_ACCESS_KEY", "reineradmin")
secret_key = os.getenv("MINIO_SECRET_KEY", "reiner12345")
bucket_name = os.getenv("MINIO_BUCKET_NAME", "reiner-logs")

# Làm sạch endpoint (loại bỏ http:// hoặc https:// nếu người dùng lỡ dán vào)
if endpoint.startswith("https://"):
    endpoint = endpoint.replace("https://", "")
elif endpoint.startswith("http://"):
    endpoint = endpoint.replace("http://", "")

# Tự động xác định chế độ bảo mật (secure):
# - Nếu endpoint chứa localhost hoặc 127.0.0.1 -> Chạy local thuần HTTP (secure=False)
# - Nếu là domain của Cloudflare Tunnel / Cloud -> Bắt buộc dùng HTTPS (secure=True)
is_local = "localhost" in endpoint or "127.0.0.1" in endpoint
secure_flag = not is_local

print(f"🔌 Đang kết nối tới MinIO Endpoint: {endpoint} (Secure Mode: {secure_flag})...")

try:
    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure_flag
    )

    # Kiểm tra xem bucket có tồn tại hay không
    if client.bucket_exists(bucket_name):
        print(f"✅ THÀNH CÔNG! Đã kết nối xuyên mây xuống MinIO thành công!")
        print(f"📦 Đang liệt kê các file trong bucket '{bucket_name}':")
        
        objects = client.list_objects(bucket_name, recursive=True)
        count = 0
        for obj in objects:
            print(f"  - File: {obj.object_name} (Kích thước: {obj.size} bytes)")
            count += 1
        
        if count == 0:
            print("  (Bucket đang trống, chưa có file nào được đẩy lên).")
    else:
        print(f"⚠️ Kết nối được tới server nhưng chưa tìm thấy bucket '{bucket_name}'.")

except Exception as e:
    print(f"❌ THẤT BẠI! Không thể kết nối: {e}")