import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey") # Change in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client["jarvis_db"]
        self.users = self.db["users"]

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    def get_user(self, username: str):
        return self.users.find_one({"username": username})

    def create_user(self, user_data):
        user_in_db = self.get_user(user_data.username)
        if user_in_db:
            return None
        
        hashed_password = self.get_password_hash(user_data.password)
        new_user = {
            "username": user_data.username,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow()
        }
        self.users.insert_one(new_user)
        return new_user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
