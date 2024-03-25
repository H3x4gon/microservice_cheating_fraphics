import uvicorn
from fastapi import FastAPI
from routers import CRouterServiceCheating

app = FastAPI()

app.include_router(CRouterServiceCheating.router)
@app.get("/")
async def root():
    return {"message": "Зайдите в эндпоинт /docs"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)