from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine, Base
import app.models 
from app.routers import auth, orders

@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "postgis";'))
        conn.commit()
    
    Base.metadata.create_all(bind=engine)
    print("PostGIS database tables initialized successfully.")
    yield

app = FastAPI(
    title="Open Delivery Network (ODN) Backend",
    description="Central AI-Powered Unified Multi-Platform Delivery Engine",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(orders.router)

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "service": "Open Delivery Network Backend Engine",
        "version": "1.0.0"
    }