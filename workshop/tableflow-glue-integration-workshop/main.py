import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import home, query_api, chart_api

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(home.router)
app.include_router(query_api.router)
app.include_router(chart_api.router)