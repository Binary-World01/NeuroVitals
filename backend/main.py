"""
Main FastAPI Application
"""
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import diagnosis, adversarial, trajectory, community, vitals, risk, outbreak, medication, config as config_router

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Neuro-Vitals: Predictive Health Intelligence System"
)

# CORS middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with standardized /api prefix
app.include_router(diagnosis.router, prefix="/api")
app.include_router(adversarial.router, prefix="/api")
app.include_router(trajectory.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(vitals.router, prefix="/api")
app.include_router(risk.router, prefix="/api")
app.include_router(outbreak.router, prefix="/api")
app.include_router(medication.router, prefix="/api")
app.include_router(config_router.router, prefix="/api")


@app.get("/api/info")
async def api_info():
    """API Information endpoint"""
    return {
        "message": "Neuro-Vitals API",
        "version": settings.VERSION,
        "docs": "/docs",
        "endpoints": {
            "diagnosis": "/api/diagnosis/analyze",
            "adversarial": "/api/adversarial/debate",
            "trajectory": "/api/trajectory/forecast",
            "community": "/api/community/heatmap",
            "vitals": {
                "save": "/api/vitals/save-vitals",
                "get": "/api/vitals/get-vitals/{user_email}",
                "latest": "/api/vitals/get-latest-vitals/{user_email}",
                "delete": "/api/vitals/delete-vitals/{user_email}",
                "health": "/api/vitals/health"
            },
            "risk": {
                "predict": "/api/risk/predict",
                "ocr": "/api/risk/ocr",
                "history": "/api/risk/history/{email}",
                "daily_log": "/api/risk/daily-log",
                "medical_record": "/api/risk/medical-record"
            },
            "outbreak": {
                "analyze": "/api/outbreak/analyze",
                "map": "/api/outbreak/map",
                "nearby": "/api/outbreak/map/nearby",
                "admin": "/api/outbreak/admin"
            },
            "medication": {
                "list": "/api/medications/{user_email}",
                "add": "/api/medications",
                "delete": "/api/medications/{id}"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }

# 1. Mount the frontend folders
# Use absolute path based on this file's location
app_dir = os.path.dirname(os.path.abspath(__file__))
public_path = os.path.abspath(os.path.join(app_dir, "..", "public"))
frontend_path = os.path.abspath(os.path.join(app_dir, "..", "frontend-app"))

# Mount public first so its files are preferred if they exist
if os.path.exists(public_path):
    app.mount("/", StaticFiles(directory=public_path, html=True), name="public")

if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")

# 2. Catch-all route to serve index.html
@app.get("/{catchall:path}")
async def serve_frontend(catchall: str):
    # Try public/index.html first
    index_file = os.path.join(public_path, "index.html")
    if not os.path.exists(index_file):
        index_file = os.path.join(frontend_path, "index.html")
        
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"error": "Frontend not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )
