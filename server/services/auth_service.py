import bcrypt
import secrets
import datetime as dt
from redis_connection import RedisClient
from typing import Dict, Any, Optional

class AuthService:
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def create_session(user_id, role, expiry_hours=24):
        """Create session in Redis and return token"""
        redis_client = RedisClient.get_client()
        if not redis_client:
            raise ConnectionError("Redis client is not initialized")
        
        token = AuthService.generate_token()

        session_data = {
            'user_id': str(user_id),
            'role': str(role),
            'created_at': dt.datetime.now().isoformat()
        }

        redis_client.hset(f"session:{token}", mapping=session_data)
        redis_client.expire(f"session:{token}", expiry_hours * 3600)
        
        return token
    
    @staticmethod
    def get_session(token: str) -> Optional[Dict[str, Any]]:
        redis_client = RedisClient.get_client()
        if not redis_client:
            return None
        
        session_data: Dict[str, str] = redis_client.hgetall(f"session:{token}")  # type: ignore
        
        if not session_data:
            return None

        return {
            'user_id': int(session_data['user_id']),
            'role': session_data['role'],
            'created_at': session_data['created_at']
        }
    
    @staticmethod
    def delete_session(token):
        redis_client = RedisClient.get_client()
        if not redis_client:
            raise ConnectionError("Redis client is not initialized")
        
        return redis_client.delete(f"session:{token}")
    
    @staticmethod
    def refresh_session(token, expiry_hours=24):
        redis_client = RedisClient.get_client()
        if not redis_client:
            raise ConnectionError("Redis client is not initialized")
        
        return redis_client.expire(f"session:{token}", expiry_hours * 3600)