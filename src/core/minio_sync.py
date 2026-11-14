import os
import json
import io
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
import requests

load_dotenv()

class MinIOSyncManager:
    def __init__(self):
        # Tự động chuyển đổi endpoint nếu chạy trong Docker network hay Local
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "reineradmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "reiner12345")
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "enterprise-agent-logs")
        
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=False
            )
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✅ [MinIO] Đã tạo thành công bucket: {self.bucket_name}")
        except Exception as e:
            print(f"⚠️ [MinIO] Không thể kết nối tới MinIO server tại {self.endpoint}: {e}")
            self.client = None

    def upload_session_logs_to_minio(self, session_id: str, logs_data: list):
        if not self.client:
            return False

        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            object_name = f"sessions/{date_str}/{session_id}.json"

            json_bytes = json.dumps(logs_data, ensure_ascii=False, indent=2).encode("utf-8")
            data_stream = io.BytesIO(json_bytes)
            file_size = len(json_bytes)

            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                file_size,
                content_type="application/json"
            )
            print(f"✅ [MinIO Sync] Đã đẩy log session [{session_id}] lên MinIO: {object_name}")
            return True
        except Exception as e:
            print(f"❌ [MinIO Error] Lỗi upload: {e}")
            return False

def sync_supabase_to_minio():
    """Hàm quét các bản ghi chưa đồng bộ trên Supabase và đẩy về MinIO local"""
    supabase_url = "https://pehksvqnwpemeifpjnnx.supabase.co/rest/v1/chat_logs?is_synced=eq.false"
    supabase_key = os.getenv("SUPABASE_KEY", "")
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}"
    }

    try:
        res = requests.get(supabase_url, headers=headers, timeout=5)
        if res.status_code != 200:
            return

        logs = res.json()
        if not logs:
            return

        session_groups = {}
        for log in logs:
            s_id = log.get("session_id")
            if s_id not in session_groups:
                session_groups[s_id] = []
            session_groups[s_id].append(log)

        minio_mgr = MinIOSyncManager()
        synced_ids = []

        for session_id, session_logs in session_groups.items():
            success = minio_mgr.upload_session_logs_to_minio(session_id, session_logs)
            if success:
                for l in session_logs:
                    if "id" in l:
                        synced_ids.append(l["id"])

        if synced_ids:
            update_url = "https://pehksvqnwpemeifpjnnx.supabase.co/rest/v1/chat_logs"
            update_headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            for record_id in synced_ids:
                requests.patch(f"{update_url}?id=eq.{record_id}", headers=update_headers, json={"is_synced": True})
            print(f"🎉 Đồng bộ thành công {len(synced_ids)} bản ghi từ Supabase về MinIO!")
    except Exception as e:
        print(f"Lỗi tiến trình sync MinIO: {e}")