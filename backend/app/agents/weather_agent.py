from typing import List, Dict, Any, Optional
import json
from app.agents.base_agent import BaseAgent
from app.core.state import TravelState, WeatherInfo
from app.services.weather_service import WeatherService
from app.messaging.protocols import MCPMessage, AgentType
from app.messaging.redis_client import RedisClient


class WeatherAgent(BaseAgent):
    """Sky Gazer - Weather forecasting agent with MCP support"""
    
    def __init__(
        self,
        name: str = "Sky Gazer",
        role: str = "Weather Forecaster",
        expertise: str = "Weather analysis, climate patterns, and travel weather recommendations",
        agent_type: AgentType = AgentType.WEATHER,
        redis_client: Optional[RedisClient] = None
    ):
        super().__init__(name, role, expertise, agent_type, redis_client)
        self.weather_service = WeatherService()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the weather agent"""
        return f"""
        You are {self.name}, a {self.role}. Your role is to:
        
        1. Analyze weather data for travel destinations
        2. Provide weather-based travel recommendations
        3. Suggest appropriate clothing and gear
        4. Warn about potential weather-related travel issues
        5. Recommend optimal times for outdoor activities
        6. Advise travelers about air quality and pollution levels
        
        Expertise: {self.expertise}
        
        Always provide practical, actionable weather advice that helps travelers prepare.
        Be concise but informative. Focus on how weather will impact the travel experience.
        
        When given weather data, create a brief summary that includes:
        - General weather overview for the trip
        - Any weather concerns or highlights
        - Clothing recommendations
        - Activity suggestions based on weather
        """
    
    async def handle_request(self, request: MCPMessage) -> Dict[str, Any]:
        """
        Handle MCP request for weather data
        
        Expected payload:
        {
            "destination": "Paris, France",
            "travel_dates": ["2025-07-01", "2025-07-02", "2025-07-03"]
        }
        
        Returns:
        {
            "weather_forecast": [...],
            "weather_summary": "...",
            "destination": "Paris, France",
            "forecast_count": 3,
            "average_temp_range": {"min": 15, "max": 25}
        }
        """
        payload = request.payload
        destination = payload.get("destination")
        travel_dates = payload.get("travel_dates", [])
        
        # Validate required fields
        if not destination:
            raise ValueError("Missing required field: destination")
        if not travel_dates:
            raise ValueError("Missing required field: travel_dates")
        
        self.log_action("Fetching weather data", f"Destination: {destination}, Dates: {len(travel_dates)}")
        
        # Send progress update
        await self._send_streaming_update(
            request.session_id,
            "progress",
            f"Fetching weather forecast for {destination}",
            progress_percent=30
        )
        
        # Fetch weather data using the weather service
        weather_forecast = await self.weather_service.get_weather_for_dates(
            location=destination,
            dates=travel_dates
        )
        
        if not weather_forecast:
            raise Exception(f"No weather data available for {destination}")
        
        # Send progress update
        await self._send_streaming_update(
            request.session_id,
            "progress",
            "Analyzing weather patterns",
            progress_percent=60
        )
        
        # Convert WeatherInfo objects to dictionaries
        weather_data = [w.dict() for w in weather_forecast]
        
        # Generate weather insights using LLM
        weather_summary = await self._generate_weather_insights_for_request(
            weather_forecast,
            destination,
            travel_dates
        )
        
        # Calculate temperature range
        avg_temp_min = sum(w.temperature_min for w in weather_forecast) / len(weather_forecast)
        avg_temp_max = sum(w.temperature_max for w in weather_forecast) / len(weather_forecast)
        
        self.log_action("Weather data retrieved", f"Forecast days: {len(weather_forecast)}")
        
        return {
            "weather_forecast": weather_data,
            "weather_summary": weather_summary,
            "destination": destination,
            "forecast_count": len(weather_forecast),
            "average_temp_range": {
                "min": round(avg_temp_min, 1),
                "max": round(avg_temp_max, 1)
            },
            "date_range": {
                "start": travel_dates[0] if travel_dates else None,
                "end": travel_dates[-1] if travel_dates else None
            }
        }
    
    async def process(self, state: TravelState) -> TravelState:
        """
        Legacy method - Process weather information for the travel destination
        Kept for backward compatibility with existing orchestration
        """
        self.log_action("Starting weather analysis", f"Destination: {state['destination']}")
        
        try:
            # Fetch weather data using the weather service
            weather_data = await self.weather_service.get_weather_for_dates(
                location=state['destination'],
                dates=state['travel_dates']
            )
            
            if weather_data:
                # Store weather data in state
                state['weather_data'] = weather_data
                state['weather_complete'] = True
                
                # Generate weather insights using LLM
                weather_summary = await self._generate_weather_insights(weather_data, state)
                
                self.add_message_to_state(
                    state, 
                    f"Weather analysis complete for {state['destination']}. {weather_summary}"
                )
                
                self.log_action("Weather analysis completed successfully")
            else:
                raise Exception("No weather data retrieved")
                
        except Exception as e:
            error_msg = f"Failed to get weather data: {str(e)}"
            self.add_error_to_state(state, error_msg)
            state['weather_complete'] = True  # Mark as complete to continue workflow
            
        return state
    
    async def _generate_weather_insights_for_request(
        self,
        weather_data: List[WeatherInfo],
        destination: str,
        travel_dates: List[str]
    ) -> str:
        """Generate weather insights for MCP request"""
        weather_summary = self._format_weather_for_llm(weather_data)
        
        user_input = f"""
        Destination: {destination}
        Travel Dates: {', '.join(travel_dates)}
        Number of Days: {len(travel_dates)}
        
        Weather Data:
        {weather_summary}
        
        Please provide a concise weather summary and travel recommendations for this trip.
        Focus on: overall conditions, packing suggestions, and any weather advisories.
        """
        
        try:
            insights = await self.invoke_llm(self.get_system_prompt(), user_input)
            return insights
        except Exception as e:
            self.log_error("Failed to generate weather insights", str(e))
            return self.get_weather_summary(weather_data)
    
    async def _generate_weather_insights(self, weather_data: List[WeatherInfo], state: TravelState) -> str:
        """Generate weather insights using the LLM (legacy method)"""
        weather_summary = self._format_weather_for_llm(weather_data)
        location_context = self.format_location_context(state)
        
        user_input = f"""
        {location_context}
        
        Weather Data:
        {weather_summary}
        
        Please provide a concise weather summary and travel recommendations for this trip.
        """
        
        try:
            insights = await self.invoke_llm(self.get_system_prompt(), user_input)
            return insights
        except Exception as e:
            self.log_error("Failed to generate weather insights", str(e))
            return "Weather data retrieved successfully, but detailed analysis unavailable."
    
    def _format_weather_for_llm(self, weather_data: List[WeatherInfo]) -> str:
        """Format weather data for LLM consumption"""
        formatted_data = []
        
        for weather in weather_data:
            ap = weather.air_pollution
            air_pollution_str = ""
            if ap:
                air_pollution_str = (
                    f"Air Quality Index: {ap.aqi}\n"
                    f"CO: {ap.co} ppm, NO: {ap.no} ppm, NO2: {ap.no2} ppm, "
                    f"O3: {ap.o3} ppm, SO2: {ap.so2} ppm\n"
                    f"PM2.5: {ap.pm2_5} µg/m³, PM10: {ap.pm10} µg/m³, NH3: {ap.nh3} µg/m³\n"
             )
            formatted_data.append(f"""
            Date: {weather.date}
            Temperature: {weather.temperature_min}°C - {weather.temperature_max}°C
            Conditions: {weather.description}
            Humidity: {weather.humidity}%
            Wind Speed: {weather.wind_speed} m/s
            Chance of Rain: {weather.precipitation_chance}%
             {air_pollution_str}
            """)
        
        return "\n".join(formatted_data)
    
    def should_process(self, state: TravelState) -> bool:
        """Check if weather processing is needed"""
        return not state.get('weather_complete', False)
    
    def get_weather_summary(self, weather_data: List[WeatherInfo]) -> str:
        """Get a quick weather summary"""
        if not weather_data:
            return "No weather data available"
        
        avg_temp_max = sum(w.temperature_max for w in weather_data) / len(weather_data)
        avg_temp_min = sum(w.temperature_min for w in weather_data) / len(weather_data)
        
        conditions = [w.description for w in weather_data]
        most_common_condition = max(set(conditions), key=conditions.count)
        
        return f"Average temperature: {avg_temp_min:.1f}°C - {avg_temp_max:.1f}°C, mostly {most_common_condition}"