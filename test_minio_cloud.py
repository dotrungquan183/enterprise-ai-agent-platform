import os
import json
from minio import Minio

client = Minio("localhost:9000", access_key="reineradmin", secret_key="reiner12345", secure=False)
objects = client.list_objects("reiner-logs", prefix="chat_logs/", recursive=True)

for obj in objects:
    print(f"Đang đọc file: {obj.object_name}")
    response = client.get_object("reiner-logs", obj.object_name)
    data = json.loads(response.read().decode('utf-8'))
    print("Nội dung thô:", data)
    response.close()
    response.release_connection()
    break # Chỉ đọc file đầu tiên để test