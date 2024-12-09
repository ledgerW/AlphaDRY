from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from routers import api
from database import create_db_and_tables

app = FastAPI()

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

# Mount the API router
app.include_router(api.router)

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
