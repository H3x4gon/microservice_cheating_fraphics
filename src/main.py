import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.logconfig import init_logging
from src.routers import CRouterServiceCheating
from src.routers import CRouterActiveSettings
from src.database import create_tables


init_logging()

app = FastAPI()

app.include_router(CRouterServiceCheating.router)
app.include_router(CRouterActiveSettings.router)

origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://localhost:8080"
]
app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
	await create_tables()


@app.get("/")
async def root():
	return {"message": "Документация по запросам доступна по пути /docs"}


@app.get("/test")
def read_root():
	return 1


if __name__ == "__main__":
	uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
