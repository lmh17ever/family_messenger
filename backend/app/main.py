from fastapi import FastAPI, Depends
import uvicorn

from app.api.routes.router import v1_router

app = FastAPI()

app.include_router(v1_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0")
