from pydantic import BaseModel, Field,field_validator
from typing import List, Optional
from datetime import date, datetime


class TravelPlanRequest(BaseModel):
    """Request model for travel planning"""
    destination: str = Field(..., description="Travel destination")
    origin: str = Field(..., description="Starting location")
    travel_dates: List[str] = Field(..., description="List of travel dates in YYYY-MM-DD format")
    travelers_count: int = Field(1, ge=1, le=20, description="Number of travelers")
    budget_range: Optional[str] = Field(None, description="Budget range (e.g., 'low', 'medium', 'high')")
    preferences: Optional[str] = Field(None, description="Additional preferences or requirements")
    
    @field_validator('travel_dates')
    def validate_dates(cls, v):
        """Validate date format and ensure dates are in the future"""
        if not v:
            raise ValueError("At least one travel date is required")
        
        validated_dates = []
        for date_str in v:
            try:
                # Parse the date to ensure it's valid
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Check if date is not in the past
                if parsed_date < date.today():
                    raise ValueError(f"Travel date {date_str} cannot be in the past")
                
                validated_dates.append(date_str)
            except ValueError as e:
                if "does not match format" in str(e):
                    raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format")
                raise e
        
        return validated_dates
    
    @field_validator('destination', 'origin')
    def validate_locations(cls, v):
        """Validate location strings"""
        if not v or len(v.strip()) < 2:
            raise ValueError("Location must be at least 2 characters long")
        return v.strip()


class WeatherRequest(BaseModel):
    """Request model for weather service"""
    location: str
    dates: List[str]


class RouteRequest(BaseModel):
    """Request model for route planning"""
    origin: str
    destination: str
    mode: str = "driving"  # driving, walking, transit, bicycling


class BudgetRequest(BaseModel):
    """Request model for budget estimation"""
    destination: str
    origin: str
    travel_dates: List[str]
    travelers_count: int
    budget_range: Optional[str] = None