import redis
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class RedisClient:
    _client: Optional[redis.Redis] = None

    @classmethod
    def init(cls) -> Optional[redis.Redis]:
        if cls._client is None:
            redis_password = os.getenv('REDIS_PASSWORD')
            
            cls._client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                password=redis_password if redis_password else None,
                decode_responses=True
            )

            try:
                cls._client.ping()
                print("✓ Redis connected successfully")
            except redis.ConnectionError as e:
                print(f"✗ Redis connection failed: {e}")
                cls._client = None
                
        return cls._client

    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        if cls._client is None:
            cls.init()
        return cls._client

    @classmethod
    def close(cls) -> None:
        if cls._client:
            cls._client.close()
            cls._client = None