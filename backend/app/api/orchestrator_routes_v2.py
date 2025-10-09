"""
FastAPI Route for Orchestrator Agent
Handles user travel queries and orchestrates multi-agent workflow with WebSocket streaming
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import asyncio
import json
import uuid
import logging
from datetime import datetime

from app.agents.orchestrator_agent import OrchestratorAgent
from app.messaging.redis_client import get_redis_client, RedisChannels
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/orchestrator", tags=["orchestrator-v2"])

# Global orchestrator instance (initialized on startup)
_orchestrator: Optional[OrchestratorAgent] = None


# ==================== REQUEST/RESPONSE MODELS ====================

class TravelQueryRequest(BaseModel):
    """Request model for travel queries"""
    query: str = Field(..., description="Natural language travel query", min_length=10)
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")
    user_id: Optional[str] = Field(None, description="Optional user ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Plan a 3-day trip to Agra from Delhi for 2 people in July with a moderate budget",
                "session_id": "session_abc123"
            }
        }


class TravelPlanResponse(BaseModel):
    """Response model for travel plan"""
    session_id: str
    status: str
    destination: Optional[str]
    travel_dates: List[str]
    weather: Optional[Dict[str, Any]]
    events: Optional[Dict[str, Any]]
    maps: Optional[Dict[str, Any]]
    budget: Optional[Dict[str, Any]]
    itinerary: Optional[Dict[str, Any]]
    messages: List[str]
    errors: List[str]
    agent_statuses: Dict[str, str]


class SessionStatusResponse(BaseModel):
    """Response model for session status"""
    session_id: str
    status: str
    progress_percent: int
    current_agent: Optional[str]
    completed_agents: List[str]
    pending_agents: List[str]


# ==================== STARTUP/SHUTDOWN ====================

async def init_orchestrator():
    """Initialize orchestrator on startup"""
    global _orchestrator
    try:
        redis_client = get_redis_client()
        await redis_client.connect()
        
        _orchestrator = OrchestratorAgent(
            redis_client=redis_client,
            gemini_api_key=settings.google_api_key,
            model_name=settings.model_name
        )
        logger.info("✅ Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        raise


async def shutdown_orchestrator():
    """Cleanup orchestrator on shutdown"""
    global _orchestrator
    if _orchestrator and _orchestrator.redis_client:
        await _orchestrator.redis_client.disconnect()
        logger.info("✅ Orchestrator shut down")


def get_orchestrator() -> OrchestratorAgent:
    """Get orchestrator instance"""
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return _orchestrator


# ==================== HTTP ENDPOINTS ====================

@router.post("/plan", response_model=TravelPlanResponse)
async def create_travel_plan(
    request: TravelQueryRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a travel plan from natural language query
    
    This endpoint processes the query asynchronously and returns the session_id.
    Use WebSocket endpoint or polling to get real-time updates.
    
    Example:
    ```json
    {
        "query": "Plan a 3-day trip to Agra from Delhi for 2 people in July",
        "session_id": "optional_session_id"
    }
    ```
    """
    try:
        orchestrator = get_orchestrator()
        
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"📝 Received travel query: {request.query[:100]}...")
        logger.info(f"   Session ID: {session_id}")
        
        # Process query asynchronously
        result = await orchestrator.process_query(
            user_query=request.query,
            session_id=session_id
        )
        
        return TravelPlanResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to process travel query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get the current status of a travel planning session
    
    Use this endpoint to poll for progress updates if not using WebSocket.
    """
    try:
        orchestrator = get_orchestrator()
        redis_client = orchestrator.redis_client
        
        # Get session state from Redis
        state = await redis_client.get_state(session_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        agent_statuses = state.get("agent_statuses", {})
        completed = [k for k, v in agent_statuses.items() if v == "completed"]
        pending = [k for k, v in agent_statuses.items() if v in ["pending", "processing"]]
        
        # Calculate progress
        total_agents = len(agent_statuses)
        completed_count = len(completed)
        progress = int((completed_count / total_agents * 100)) if total_agents > 0 else 0
        
        current_agent = pending[0] if pending else None
        
        return SessionStatusResponse(
            session_id=session_id,
            status=state.get("workflow_status", "unknown"),
            progress_percent=progress,
            current_agent=current_agent,
            completed_agents=completed,
            pending_agents=pending
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/result")
async def get_session_result(session_id: str):
    """
    Get the final result of a completed travel planning session
    """
    try:
        orchestrator = get_orchestrator()
        redis_client = orchestrator.redis_client
        
        # Get session state from Redis
        state = await redis_client.get_state(session_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if state.get("workflow_status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Session not completed. Current status: {state.get('workflow_status')}"
            )
        
        return {
            "session_id": session_id,
            "status": state.get("workflow_status"),
            "destination": state.get("destination"),
            "travel_dates": state.get("travel_dates"),
            "weather": state.get("weather_data"),
            "events": state.get("events_data"),
            "maps": state.get("maps_data"),
            "budget": state.get("budget_data"),
            "itinerary": state.get("itinerary_data"),
            "messages": state.get("messages", []),
            "errors": state.get("errors", []),
            "agent_statuses": state.get("agent_statuses", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its associated data
    """
    try:
        orchestrator = get_orchestrator()
        redis_client = orchestrator.redis_client
        
        # Delete session state
        await redis_client.delete_state(session_id)
        
        return {"message": f"Session {session_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WEBSOCKET ENDPOINT ====================

@router.websocket("/ws/{session_id}")
async def websocket_streaming(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time travel planning updates
    
    Connect to this endpoint to receive streaming updates during travel plan creation.
    
    Message format:
    ```json
    {
        "type": "progress" | "agent_update" | "completed" | "error",
        "agent": "orchestrator" | "weather" | "events" | "maps" | "budget" | "itinerary",
        "message": "Status message",
        "progress_percent": 50,
        "data": { ... },
        "timestamp": "2025-01-01T00:00:00Z"
    }
    ```
    """
    await websocket.accept()
    logger.info(f"🔌 WebSocket connected for session: {session_id}")
    
    try:
        orchestrator = get_orchestrator()
        redis_client = orchestrator.redis_client
        
        # Subscribe to streaming updates for this session
        streaming_channel = RedisChannels.get_streaming_channel(session_id)
        
        # Message handler
        async def handle_message(message: Dict[str, Any]):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
        
        # Subscribe to Redis channel
        subscription_id = await redis_client.subscribe(streaming_channel, handle_message)
        
        logger.info(f"📡 Subscribed to streaming updates for session: {session_id}")
        
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "Connected to travel planning stream",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and listen for client messages
        try:
            while True:
                # Wait for client message (or timeout)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300)
                
                # Handle client messages (e.g., ping)
                try:
                    client_msg = json.loads(data)
                    if client_msg.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                except json.JSONDecodeError:
                    pass
                    
        except asyncio.TimeoutError:
            # Connection timeout after 5 minutes of inactivity
            logger.info(f"⏱️ WebSocket timeout for session: {session_id}")
            await websocket.send_json({
                "type": "timeout",
                "message": "Connection timeout due to inactivity",
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass
    finally:
        # Cleanup subscription
        try:
            await redis_client.unsubscribe(subscription_id)
            logger.info(f"🔕 Unsubscribed from streaming updates for session: {session_id}")
        except:
            pass
        
        try:
            await websocket.close()
        except:
            pass


# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check():
    """
    Health check endpoint for orchestrator service
    """
    try:
        orchestrator = get_orchestrator()
        redis_connected = orchestrator.redis_client.is_connected()
        
        return {
            "status": "healthy" if redis_connected else "degraded",
            "orchestrator": "ready",
            "redis": "connected" if redis_connected else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# ==================== EXPORT STARTUP/SHUTDOWN HANDLERS ====================

async def startup():
    """Startup handler for FastAPI"""
    await init_orchestrator()


async def shutdown():
    """Shutdown handler for FastAPI"""
    await shutdown_orchestrator()


# Export handlers for use in main.py
__all__ = ["router", "startup", "shutdown"]