from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Test API", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

logger.info("✅ App initialized successfully")

@app.get("/")
def root():
    logger.info("📍 Root endpoint called")
    return {
        "status": "running",
        "message": "Test backend is working!",
        "port": os.getenv("PORT", "8000"),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/echo")
def echo(data: dict):
    logger.info(f"📥 Received: {data}")
    return {"received": data, "echo": "success"}

@app.on_event("startup")
async def startup():
    logger.info(f"🚀 Server started on port {os.getenv('PORT', '8000')}")
    logger.info("✅ Ready to accept requests")

@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 Server shutting down")