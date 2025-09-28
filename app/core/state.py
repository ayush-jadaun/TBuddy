from typing import Dict, List, Any, Optional, TypedDict
from pydantic import BaseModel
from datetime import datetime, date


class WeatherInfo(BaseModel):
    """Weather information structure"""
    date: str
    temperature_max: float
    temperature_min: float
    description: str
    humidity: int
    wind_speed: float
    precipitation_chance: int


class RouteInfo(BaseModel):
    """Route information structure"""
    distance: str
    duration: str
    steps: List[str]
    traffic_info: Optional[str] = None
    transport_mode: str = "driving"


class BudgetBreakdown(BaseModel):
    """Budget breakdown structure"""
    transportation: float
    accommodation: float
    food: float
    activities: float
    total: float
    currency: str = "USD"


class ItineraryDay(BaseModel):
    """Single day itinerary structure"""
    day: int
    date: str
    activities: List[str]
    notes: str
    estimated_cost: float


class TravelState(TypedDict):
    """Shared state across all agents"""
    # Input parameters
    destination: str
    origin: str
    travel_dates: List[str]
    travelers_count: int
    budget_range: Optional[str]
    
    # Agent outputs
    weather_data: Optional[List[WeatherInfo]]
    route_data: Optional[RouteInfo]
    budget_data: Optional[BudgetBreakdown]
    itinerary_data: Optional[List[ItineraryDay]]
    
    # Processing status
    weather_complete: bool
    maps_complete: bool
    budget_complete: bool
    itinerary_complete: bool
    
    # Messages and errors
    messages: List[str]
    errors: List[str]
    
    # Final summary
    trip_summary: Optional[str]


def create_initial_state(
    destination: str,
    origin: str,
    travel_dates: List[str],
    travelers_count: int = 1,
    budget_range: Optional[str] = None
) -> TravelState:
    """Create initial state for the travel planning workflow"""
    return TravelState(
        destination=destination,
        origin=origin,
        travel_dates=travel_dates,
        travelers_count=travelers_count,
        budget_range=budget_range,
        weather_data=None,
        route_data=None,
        budget_data=None,
        itinerary_data=None,
        weather_complete=False,
        maps_complete=False,
        budget_complete=False,
        itinerary_complete=False,
        messages=[],
        errors=[],
        trip_summary=None
    )