import asyncio
import sys

sys.path.insert(0, "backend")

from sqlalchemy import select
from app.core.database import async_session_factory, engine
from app.core.security import hash_password
from app.models.base import Base
from app.models.user import User


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        stmt = select(User).where(User.email == "demo@planmytrip.ai")
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            user = User(
                email="demo@planmytrip.ai",
                hashed_password=hash_password("password123"),
                is_active=True,
            )
            session.add(user)
            await session.commit()
            print("Demo user created: demo@planmytrip.ai / password123")
        else:
            print("Demo user already exists: demo@planmytrip.ai")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
