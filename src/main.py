import uvicorn
from fastapi import FastAPI
from routers import CRouterModels

app = FastAPI()

app.include_router(CRouterModels.router)
@app.get("/test")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)