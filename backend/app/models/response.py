from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.state import WeatherInfo, RouteInfo, BudgetBreakdown, ItineraryDay


class TravelPlanResponse(BaseModel):
    """Response model for complete travel plan"""
    success: bool
    message: str
    trip_summary: Optional[str] = None
    weather: Optional[List[WeatherInfo]] = None
    route: Optional[RouteInfo] = None
    budget: Optional[BudgetBreakdown] = None
    itinerary: Optional[List[ItineraryDay]] = None
    errors: List[str] = []
    processing_time: Optional[float] = None


class WeatherResponse(BaseModel):
    """Response model for weather data"""
    success: bool
    data: Optional[List[WeatherInfo]] = None
    error: Optional[str] = None


class RouteResponse(BaseModel):
    """Response model for route data"""
    success: bool
    data: Optional[RouteInfo] = None
    error: Optional[str] = None


class BudgetResponse(BaseModel):
    """Response model for budget data"""
    success: bool
    data: Optional[BudgetBreakdown] = None
    error: Optional[str] = None


class ItineraryResponse(BaseModel):
    """Response model for itinerary data"""
    success: bool
    data: Optional[List[ItineraryDay]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: str
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class StatusResponse(BaseModel):
    """Response model for system status"""
    status: str
    timestamp: str
    agents: Dict[str, str]
    available_features: List[str]