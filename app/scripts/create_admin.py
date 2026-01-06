"""
Script to create initial admin user.
Run with: python -m app.scripts.create_admin
"""
import asyncio
import sys

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import async_session_maker
from app.models import User


async def create_admin(username: str = "admin", password: str = "admin123") -> None:
    """Create an admin user if not exists."""
    async with async_session_maker() as session:
        # Check if admin exists
        result = await session.execute(
            select(User).where(User.username == username)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"User '{username}' already exists.")
            return
        
        # Create admin user
        admin = User(
            username=username,
            password_hash=get_password_hash(password),
            role="ADMIN",
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Admin user '{username}' created successfully with password '{password}'")


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
    asyncio.run(create_admin(username, password))
