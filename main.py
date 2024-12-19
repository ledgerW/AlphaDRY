from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from dotenv import load_dotenv
from routers import api
from database import create_db_and_tables

load_dotenv()

app = FastAPI(name="AlphaDRY")


# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_db_and_tables(force_reset=False)


# Mount the API router
app.include_router(api.router)

# Serve static files from the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory=".")


@app.get("/")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "api_key": os.getenv("API_KEY", "")
    })


if __name__ == "__main__":
    # Use port 80 for deployment or 2024 as fallback
    port = int(os.environ.get('PORT', 80))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
