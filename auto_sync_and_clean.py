import os
import json
import io
import time
from datetime import datetime
from minio import Minio
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = "https://pehksvqnwpemeifpjnnx.supabase.co/rest/v1/chat_logs"
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

MINIO_ENDPOINT = "127.0.0.1:9000"
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "reineradmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "reiner12345")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "reiner-logs")

def get_minio_client():
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

def sync_and_purge():
    if not SUPABASE_KEY:
        print("❌ Lỗi: Chưa cấu hình SUPABASE_KEY trong file .env!")
        return

    try:
        # 1. Lấy toàn bộ dữ liệu trên Supabase
        res = requests.get(SUPABASE_URL, headers=HEADERS, timeout=5)
        if res.status_code != 200:
            print(f"⚠️ [Supabase Fetch Error]: Status {res.status_code} - {res.text}")
            return

        logs = res.json()
        if not logs:
            print("✨ Supabase đang trống, không có dữ liệu mới.")
            return

        print(f"📦 Phát hiện {len(logs)} bản ghi trên Supabase. Đang đẩy về MinIO...")

        # 2. Đẩy dữ liệu xuống MinIO local
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)

        session_groups = {}
        for log in logs:
            s_id = log.get("session_id", "default_session")
            if s_id not in session_groups:
                session_groups[s_id] = []
            session_groups[s_id].append(log)

        has_pulled = False
        for session_id, session_logs in session_groups.items():
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            object_name = f"chat_logs/auto_pull_{session_id}_{timestamp_str}.json"

            json_bytes = json.dumps(session_logs, ensure_ascii=False, indent=2).encode("utf-8")
            data_stream = io.BytesIO(json_bytes)
            
            minio_client.put_object(
                BUCKET_NAME,
                object_name,
                data_stream,
                len(json_bytes),
                content_type="application/json"
            )
            print(f"✅ Đã lưu session [{session_id}] xuống MinIO: {object_name}")
            has_pulled = True

        # 3. Kéo về xong -> Xóa sạch toàn bộ bảng chat_logs trên Supabase bằng câu lệnh điều kiện vạn năng (id=not.is.null)
        if has_pulled:
            purge_url = f"{SUPABASE_URL}?id=not.is.null"
            # Thêm header Prefer: return=representation để buộc Supabase trả về kết quả sau khi xóa
            purge_headers = HEADERS.copy()
            purge_headers["Prefer"] = "return=representation"
            
            purge_res = requests.delete(purge_url, headers=purge_headers, timeout=5)
            
            if purge_res.status_code < 400:
                print(f"🧹 Đã dọn dẹp và xóa trắng sạch sẽ bảng chat_logs trên Supabase thành công!\n")
            else:
                print(f"⚠️ Không thể xóa sạch Supabase: Status {purge_res.status_code} - {purge_res.text}\n")

    except Exception as e:
        print(f"❌ [Sync & Purge Error]: {e}\n")

if __name__ == "__main__":
    print("🚀 Tiến trình Auto-Sync & Purge đang chạy (Quét -> Đẩy MinIO -> Xóa trắng Supabase mỗi 5 giây)...")
    while True:
        sync_and_purge()
        time.sleep(5)