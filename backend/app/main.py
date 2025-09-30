from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from datetime import datetime

from app.config.settings import settings
from app.api.routes import router as legacy_router
from app.api.orchestrator_routes import router as orchestrator_router
from app.models.response import ErrorResponse
from app.messaging.redis_client import get_redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    # Startup
    logger.info(f"🎪 Starting {settings.app_name} v2.0")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Test Redis connection for orchestrator
    try:
        redis_client = get_redis_client()
        await redis_client.connect()
        is_healthy = await redis_client.health_check()
        
        if is_healthy:
            logger.info("✅ Redis connection established (Orchestrator enabled)")
            redis_info = await redis_client.get_info()
            logger.info(f"   Redis version: {redis_info.get('version', 'unknown')}")
        else:
            logger.warning("⚠️ Redis connection unhealthy (Orchestrator disabled)")
        
        await redis_client.disconnect()
        
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {str(e)}")
        logger.warning("⚠️ Orchestrator features disabled. Legacy API still available.")
    
    logger.info(f"🚀 API Documentation: http://{settings.host}:{settings.port}/docs")
    logger.info(f"📊 Status endpoint: http://{settings.host}:{settings.port}/status")
    
    yield
    
    # Shutdown
    logger.info(f"👋 Shutting down {settings.app_name}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
    🎪 **Ringmaster Round Table** - AI-Powered Travel Planning System
    
    ## Features
    - 🤖 Multi-agent orchestration with Redis pub/sub
    - ⚡ Parallel agent execution for faster responses
    - 📡 Real-time streaming updates
    - 🌤️ Weather forecasting
    - 🗺️ Route planning & navigation
    - 🎭 Event discovery
    - 💰 Budget estimation
    - 📅 Itinerary generation
    
    ## API Versions
    - **v1 (Legacy)**: `/api/v1/*` - Direct agent endpoints
    - **v2 (Orchestrator)**: `/api/v1/plan-trip*` - Orchestrated workflow
    """,
    version="2.0.0",
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(legacy_router, prefix="/api/v1", tags=["Legacy API"])
app.include_router(orchestrator_router, tags=["Orchestrator API"])


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            details={"message": str(exc) if settings.debug else "An error occurred"}
        ).dict()
    )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "app": settings.app_name,
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "orchestrated_planning": "NEW - Parallel agent execution with Redis",
            "streaming_updates": "NEW - Real-time progress notifications",
            "legacy_api": "Available for backward compatibility"
        },
        "endpoints": {
            "orchestrator": {
                "plan_trip": "/api/v1/plan-trip (POST)",
                "plan_trip_stream": "/api/v1/plan-trip/stream (POST)",
                "session_status": "/api/v1/session/{session_id} (GET)",
                "cancel_session": "/api/v1/session/{session_id} (DELETE)"
            },
            "legacy": {
                "weather": "/api/v1/weather (POST)",
                "route": "/api/v1/route (POST)",
                "events": "/api/v1/events (POST)",
                "budget": "/api/v1/budget (POST)",
                "itinerary": "/api/v1/itinerary (POST)",
                "full_plan": "/api/v1/plan (POST)"
            }
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/status")
async def status():
    """Enhanced status endpoint with orchestrator information"""
    
    # Check Redis health
    redis_status = "unknown"
    redis_info = {}
    try:
        redis_client = get_redis_client()
        await redis_client.connect()
        is_healthy = await redis_client.health_check()
        redis_status = "healthy" if is_healthy else "unhealthy"
        redis_info = await redis_client.get_info()
        await redis_client.disconnect()
    except Exception as e:
        redis_status = "disconnected"
        redis_info = {"error": str(e)}
    
    return {
        "app_status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "orchestrator": {
            "enabled": redis_status == "healthy",
            "redis_status": redis_status,
            "redis_info": redis_info,
            "workers": {
                "weather": "1 replicas",
                "events": "1 replicas",
                "maps": "1 replicas",
                "budget": "1 replica",
                "itinerary": "1 replica"
            }
        },
        "agents": {
            "weather": {
                "name": "Sky Gazer",
                "status": "active",
                "service": "OpenWeatherMap",
                "capabilities": ["weather forecasts", "climate analysis", "travel recommendations"],
                "timeout": f"{settings.timeout_weather}ms"
            },
            "events": {
                "name": "Buzzfinder",
                "status": "active",
                "service": "OpenWeb Ninja",
                "capabilities": ["event discovery", "venue information", "category filtering"],
                "timeout": f"{settings.timeout_events}ms"
            },
            "maps": {
                "name": "Trailblazer",
                "status": "active",
                "service": "OpenRouteService",
                "capabilities": ["route planning", "transportation comparison", "navigation guidance"],
                "timeout": f"{settings.timeout_maps}ms"
            },
            "budget": {
                "name": "Quartermaster",
                "status": "active",
                "service": "Internal Cost Database",
                "capabilities": ["budget estimation", "cost breakdown", "expense planning"],
                "timeout": f"{settings.timeout_budget}ms"
            },
            "itinerary": {
                "name": "Chronomancer",
                "status": "active",
                "service": "Gemini AI",
                "capabilities": ["day planning", "activity scheduling", "timeline optimization"],
                "timeout": f"{settings.timeout_itinerary}ms"
            }
        },
        "configuration": {
            "model": settings.model_name,
            "temperature": settings.temperature,
            "max_parallel_agents": settings.max_parallel_agents,
            "orchestrator_timeout": f"{settings.orchestrator_timeout}ms",
            "streaming_enabled": settings.streaming_enabled
        }
    }


@app.get("/health")
async def health_check():
    """Simple health check for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name}...")
    logger.info(f"OpenWeb Ninja API Key configured: {'Yes' if settings.openweb_ninja_api_key else 'No'}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )