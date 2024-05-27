from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from models.db_models import Base

import asyncio

# Замените эти значения на ваши данные для подключения к базе данных
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/Microservice"

# Создание асинхронного движка
engine = create_async_engine(DATABASE_URL, echo=True)  # Вывод SQL-запросов в консоль (для отладки)

# Создание асинхронной фабрики сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Функция для создания всех таблиц
async def create_tables():
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)


# Функция для получения сессии
async def get_session() -> AsyncSession:
	async with async_session() as session:
		yield session
