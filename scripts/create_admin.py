import asyncio
import sys
import os
import argparse

# Add project root to path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_admin(username, password, telegram_id=None):
    async with AsyncSessionLocal() as session:
        # Check if exists
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            print(f"❌ User '{username}' already exists.")
            return

        hashed = get_password_hash(password)
        new_user = User(
            username=username,
            hashed_password=hashed,
            role=UserRole.ADMIN,
            name="Super Admin",
            telegram_id=telegram_id or 0, # Dummy for web-only
            phone="+7000000000"
        )
        session.add(new_user)
        await session.commit()
        print(f"✅ Created Admin: {username} / {password}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="Admin username")
    parser.add_argument("password", help="Admin password")
    args = parser.parse_args()
    
    asyncio.run(create_admin(args.username, args.password))
