# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.users_router import user_router
from backend.places_router import places_router
from backend.database import create_tables, delete_tables
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    #await delete_tables()
    await create_tables()
    print("База данных готова к работе")
    yield
    print("Выключение")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://172.18.43.254:8080",
        "http://localhost:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api")
app.include_router(places_router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Places API работает!", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "SQLite"}