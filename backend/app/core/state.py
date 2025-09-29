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




# Add this to your app/core/state.py file

from dataclasses import dataclass
from typing import Optional

@dataclass
class EventInfo:
    """Event information data class"""
    name: str
    date: str  # YYYY-MM-DD format
    time: str  # HH:MM format
    venue: str
    address: str
    category: str  # music, sports, arts, theatre, etc.
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    currency: str = "USD"
    description: str = ""
    url: str = ""
    image_url: str = ""
    
    def dict(self):
        """Convert to dictionary"""
        return {
            "name": self.name,
            "date": self.date,
            "time": self.time,
            "venue": self.venue,
            "address": self.address,
            "category": self.category,
            "price_min": self.price_min,
            "price_max": self.price_max,
            "currency": self.currency,
            "description": self.description,
            "url": self.url,
            "image_url": self.image_url
        }
    
    @property
    def price_range(self) -> str:
        """Get formatted price range"""
        if self.price_min is None and self.price_max is None:
            return "Price TBA"
        elif self.price_min == 0:
            return "Free"
        elif self.price_min == self.price_max:
            return f"{self.currency} {self.price_min}"
        else:
            return f"{self.currency} {self.price_min}-{self.price_max}"
    
    @property
    def datetime_str(self) -> str:
        """Get formatted date and time"""
        if self.time:
            return f"{self.date} at {self.time}"
        return self.date
    
    def is_free(self) -> bool:
        """Check if event is free"""
        return self.price_min == 0
    
    def is_on_date(self, date: str) -> bool:
        """Check if event is on specific date"""
        return self.date == date