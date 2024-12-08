from fastapi import FastAPI
from routers import api

app = FastAPI(title='AlphaDRY', version='0.1.0')

app.include_router(api.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
    