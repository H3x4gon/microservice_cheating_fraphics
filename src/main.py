import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

from fastapi import FastAPI
from routers import CRouterServiceCheating

from database import create_tables
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
	await create_tables()
	print("База создана и готова к работе")
	yield
	print("Выключение")


app = FastAPI(lifespan=lifespan)

app.include_router(CRouterServiceCheating.router)


@app.get("/")
async def root():
	return {"message": "Зайдите в эндпоинт /docs"}


if __name__ == "__main__":
	uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
