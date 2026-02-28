from pydantic import BaseModel
from typing import Optional, List
import boto3
import json
import os

class User(BaseModel):
    id: Optional[int]
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

# === S3 Setup ===
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "your-bucket-name")
S3_META_FILE = os.environ.get("S3_USER_META_FILE", "users_metadata.json")
s3_client = boto3.client("s3")

def load_all_users() -> List[User]:
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_META_FILE)
        users_raw = json.loads(response['Body'].read().decode('utf-8'))
        return [User(**data) for data in users_raw]
    except s3_client.exceptions.NoSuchKey:
        return []
    except Exception as e:
        print("❌ Error loading user metadata:", e)
        return []

def save_all_users(users: List[User]):
    try:
        users_json = [user.dict() for user in users]
        s3_client.put_object(Bucket=S3_BUCKET, Key=S3_META_FILE, Body=json.dumps(users_json))
        print("✅ User metadata saved to S3")
    except Exception as e:
        print("❌ Error saving user metadata:", e)

def add_user_metadata(user: User):
    users = load_all_users()
    users.append(user)
    save_all_users(users)
