import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

from fastapi import FastAPI
from routers import CRouterServiceCheating
from routers import CRouterActiveSettings

from database import create_tables
from contextlib import asynccontextmanager
from logconfig import init_logging

import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
	await create_tables()
	print("База создана и готова к работе")
	yield
	print("Выключение")

init_logging()

app = FastAPI(lifespan=lifespan)

app.include_router(CRouterServiceCheating.router)
app.include_router(CRouterActiveSettings.router)

@app.get("/")
async def root():
	return {"message": "Зайдите в эндпоинт /docs"}


if __name__ == "__main__":
	uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
