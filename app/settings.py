import urllib.parse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.utils.base64_decode import decode_env
import aioredis

data = decode_env()
# 设置数据库连接参数
username = data.get('MYSQL_USER')
password = data.get('MYSQL_PASSWORD')
hostname = data.get('MYSQL_HOST')
port = data.get('MYSQL_PORT')
database_name = data.get('MYSQL_NAME')

# URL 编码密码部分
actual_password = urllib.parse.quote_plus(password)

# 创建数据库连接 URL
DATABASE_URL = f"mysql+aiomysql://{username}:{actual_password}@{hostname}:{port}/{database_name}"

# 初始化引擎和会话
engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# redis.py

class RedisClient:
    def __init__(self, url: str):
        self._url = url
        self._redis = None

    async def connect(self):
        self._redis = await aioredis.from_url(self._url)

    async def close(self):
        self._redis.close()
        await self._redis.wait_closed()

    @property
    def redis(self):
        return self._redis

redis_client = RedisClient("redis://localhost:6379")

async def get_redis():
    return redis_client.redis
