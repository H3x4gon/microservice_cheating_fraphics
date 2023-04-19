from fastapi import FastAPI

from .routers import CRouterModels

app = FastAPI()

app.include_router(CRouterModels.router)


@app.get("/test")
async def root():
    return {"message": "Hello World"}
