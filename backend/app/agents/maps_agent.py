from typing import Dict, Optional, Any, List
import asyncio
from app.agents.base_agent import BaseAgent
from app.core.state import TravelState, RouteInfo
from app.services.maps_service import MapsService
from app.messaging.protocols import MCPMessage, AgentType
from app.messaging.redis_client import RedisClient


class MapsAgent(BaseAgent):
    """Trailblazer - Route planning and navigation agent with MCP support"""
    
    def __init__(
        self,
        name: str = "Trailblazer",
        role: str = "Route Planner & Navigator",
        expertise: str = "Route optimization, transportation analysis, and travel logistics",
        agent_type: AgentType = AgentType.MAPS,
        redis_client: Optional[RedisClient] = None
    ):
        super().__init__(name, role, expertise, agent_type, redis_client)
        self.maps_service = MapsService()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the maps agent"""
        return f"""
You are {self.name}, a {self.role}. Your role is to:

1. Analyze route options between origin and destination
2. Compare different transportation modes (driving, walking, cycling)
3. Provide practical travel recommendations based on distance and duration
4. Suggest optimal transportation methods considering factors like time, cost, and convenience
5. Identify potential travel challenges or considerations

Expertise: {self.expertise}

Always provide practical, actionable route advice that helps travelers make informed decisions.
Be concise but informative. Focus on how route choices will impact the overall travel experience.

When given route data, create a brief analysis that includes:
- Recommended transportation mode and reasoning
- Journey overview with key details
- Any notable considerations or tips
- Alternative options if relevant

Keep responses brief - 2-3 sentences maximum unless more detail is specifically requested.
        """
    
    async def handle_request(self, request: MCPMessage) -> Dict[str, Any]:
        """
        Handle MCP request for route data
        
        Expected payload:
        {
            "origin": "New Delhi, India",
            "destination": "Agra, India",
            "transport_mode": "driving",  # optional, default: "driving"
            "include_alternatives": true,  # optional, default: true
            "include_travel_options": false,  # optional, default: false
            "travel_date": "2025-07-01",  # required if include_travel_options=true
            "checkin_date": "2025-07-01",  # optional
            "checkout_date": "2025-07-05"  # optional
        }
        
        Returns:
        {
            "primary_route": RouteInfo dict,
            "alternative_routes": {mode: RouteInfo dict},
            "route_analysis": "LLM-generated insights",
            "recommended_mode": "driving",
            "comparison": {mode: {distance, duration, mode}},
            "travel_options": {...}  # if requested
        }
        """
        payload = request.payload
        origin = payload.get("origin")
        destination = payload.get("destination")
        transport_mode = payload.get("transport_mode", "driving")
        include_alternatives = payload.get("include_alternatives", True)
        include_travel_options = payload.get("include_travel_options", False)
        
        # Validate required fields
        if not origin:
            raise ValueError("Missing required field: origin")
        if not destination:
            raise ValueError("Missing required field: destination")
        
        self.log_action("Fetching route data", f"{origin} → {destination} ({transport_mode})")
        
        # Send progress update
        await self._send_streaming_update(
            request.session_id,
            "progress",
            f"Calculating route from {origin} to {destination}",
            progress_percent=20
        )
        
        # Get primary route
        primary_route = await self.maps_service.get_route_between_locations(
            origin=origin,
            destination=destination,
            transport_mode=transport_mode
        )
        
        if not primary_route:
            self.log_error("Primary route fetch failed", "Using fallback")
            primary_route = self._create_fallback_route_info(origin, destination, transport_mode)
        
        result = {
            "primary_route": primary_route.dict(),
            "origin": origin,
            "destination": destination,
            "requested_mode": transport_mode
        }
        
        # Get alternative routes if requested
        alternative_routes = {}
        if include_alternatives:
            await self._send_streaming_update(
                request.session_id,
                "progress",
                "Analyzing alternative transportation options",
                progress_percent=40
            )
            
            alternative_routes = await self._get_alternative_routes_for_request(
                origin, destination, transport_mode
            )
            
            result["alternative_routes"] = {
                mode: (route.dict() if route else None)
                for mode, route in alternative_routes.items()
            }
        
        # Get travel options if requested (flights, trains, buses, hotels)
        if include_travel_options:
            await self._send_streaming_update(
                request.session_id,
                "progress",
                "Fetching travel options (flights, trains, buses, hotels)",
                progress_percent=60
            )
            
            travel_date = payload.get("travel_date")
            checkin = payload.get("checkin_date")
            checkout = payload.get("checkout_date")
            
            if not travel_date:
                self.log_error("Travel options requested but no travel_date provided", "Skipping")
            else:
                travel_options = await self.maps_service.get_travel_options(
                    origin=origin,
                    destination=destination,
                    date=travel_date,
                    checkin=checkin,
                    checkout=checkout
                )
                result["travel_options"] = travel_options
        
        # Generate analysis
        await self._send_streaming_update(
            request.session_id,
            "progress",
            "Generating route recommendations",
            progress_percent=80
        )
        
        route_analysis = await self._generate_route_insights_for_request(
            primary_route,
            alternative_routes,
            origin,
            destination
        )
        
        result["route_analysis"] = route_analysis
        result["recommended_mode"] = self._determine_recommended_mode(
            primary_route, alternative_routes
        )
        result["comparison"] = self._create_route_comparison(
            primary_route, alternative_routes
        )
        
        self.log_action(
            "Route data retrieved", 
            f"Primary: {transport_mode}, Alternatives: {len(alternative_routes)}"
        )
        
        return result
    
    async def process(self, state: TravelState) -> TravelState:
        """Legacy method - Process route information for the travel itinerary"""
        self.log_action("Starting route analysis", f"From {state['origin']} to {state['destination']}")
        
        try:
            transport_mode = state.get('preferred_transport', 'driving')
            
            # Get primary route
            primary_route = await self.maps_service.get_route_between_locations(
                origin=state['origin'],
                destination=state['destination'],
                transport_mode=transport_mode
            )
            
            if primary_route:
                state['route_data'] = primary_route.dict()
                
                # Get alternative routes
                alternative_routes = await self._get_alternative_routes(state)
                
                # Generate insights
                route_analysis = await self._generate_route_insights(
                    primary_route, alternative_routes, state
                )
                
                self.add_message_to_state(
                    state, 
                    f"Route analysis complete. {route_analysis}"
                )
                
                self.log_action("Route analysis completed successfully")
            else:
                fallback_route = self._create_fallback_route_info(
                    state['origin'], state['destination'], transport_mode
                )
                state['route_data'] = fallback_route.dict()
                
                self.add_message_to_state(
                    state,
                    f"Basic route information available for {state['origin']} to {state['destination']}"
                )
                
                self.log_action("Used fallback route information")
                
        except Exception as e:
            error_msg = f"Failed to get route information: {str(e)}"
            self.add_error_to_state(state, error_msg)
            
            try:
                fallback_route = self._create_fallback_route_info(
                    state['origin'], state['destination'], 'driving'
                )
                state['route_data'] = fallback_route.dict()
            except:
                pass
                
        finally:
            state['maps_complete'] = True
            
        return state
    
    def _create_fallback_route_info(
        self, 
        origin: str, 
        destination: str, 
        transport_mode: str
    ) -> RouteInfo:
        """Create basic route information when API calls fail"""
        return RouteInfo(
            distance="Distance calculation unavailable",
            duration="Duration estimation unavailable",
            steps=[f"Travel from {origin} to {destination}"],
            traffic_info=None,
            transport_mode=transport_mode
        )
    
    async def _get_alternative_routes_for_request(
        self,
        origin: str,
        destination: str,
        primary_mode: str
    ) -> Dict[str, Optional[RouteInfo]]:
        """Get alternative transportation routes for MCP request"""
        self.log_action("Fetching alternative transportation options")
        
        all_modes = ["driving", "walking", "cycling"]
        alternative_modes = [mode for mode in all_modes if mode != primary_mode]
        
        try:
            tasks = [
                self.maps_service.get_route_between_locations(origin, destination, mode)
                for mode in alternative_modes
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            alternatives = {}
            for mode, result in zip(alternative_modes, results):
                if not isinstance(result, Exception) and result:
                    alternatives[mode] = result
                else:
                    alternatives[mode] = None
            
            return alternatives
            
        except Exception as e:
            self.log_error("Failed to get alternative routes", str(e))
            return {}
    
    async def _get_alternative_routes(self, state: TravelState) -> Dict[str, Optional[RouteInfo]]:
        """Get alternative transportation routes (legacy)"""
        primary_mode = state.get('preferred_transport', 'driving')
        return await self._get_alternative_routes_for_request(
            state['origin'],
            state['destination'],
            primary_mode
        )
    
    async def _generate_route_insights_for_request(
        self,
        primary_route: RouteInfo,
        alternative_routes: Dict[str, Optional[RouteInfo]],
        origin: str,
        destination: str
    ) -> str:
        """Generate route insights using LLM for MCP request"""
        route_summary = self._format_routes_for_llm(primary_route, alternative_routes)
        
        user_input = f"""
Origin: {origin}
Destination: {destination}

Route Analysis:
{route_summary}

Please provide a concise route recommendation and travel analysis for this journey.
Consider factors like convenience, time efficiency, and practical considerations.
Keep it brief - 2-3 sentences maximum.
        """
        
        try:
            insights = await self.invoke_llm(self.get_system_prompt(), user_input)
            return insights
        except Exception as e:
            self.log_error("Failed to generate route insights", str(e))
            return f"Primary route: {primary_route.distance} in {primary_route.duration} by {primary_route.transport_mode}"
    
    async def _generate_route_insights(
        self, 
        primary_route: RouteInfo,
        alternative_routes: Dict[str, Optional[RouteInfo]], 
        state: TravelState
    ) -> str:
        """Generate route insights using the LLM (legacy)"""
        return await self._generate_route_insights_for_request(
            primary_route,
            alternative_routes,
            state['origin'],
            state['destination']
        )
    
    def _format_routes_for_llm(
        self, 
        primary_route: RouteInfo, 
        alternative_routes: Dict[str, Optional[RouteInfo]]
    ) -> str:
        """Format route data for LLM consumption"""
        formatted_data = [f"""
PRIMARY ROUTE ({primary_route.transport_mode.upper()}):
Distance: {primary_route.distance}
Duration: {primary_route.duration}
Transport: {primary_route.transport_mode}
        """]
        
        for mode, route in alternative_routes.items():
            if route:
                formatted_data.append(f"""
ALTERNATIVE ({mode.upper()}):
Distance: {route.distance}
Duration: {route.duration}
Transport: {route.transport_mode}
                """)
        
        return "\n".join(formatted_data)
    
    def _determine_recommended_mode(
        self,
        primary_route: RouteInfo,
        alternative_routes: Dict[str, Optional[RouteInfo]]
    ) -> str:
        """Determine the recommended transportation mode"""
        if primary_route:
            return primary_route.transport_mode
        
        if alternative_routes:
            for mode, route in alternative_routes.items():
                if route:
                    return mode
        
        return "driving"
    
    def _create_route_comparison(
        self,
        primary_route: RouteInfo,
        alternative_routes: Dict[str, Optional[RouteInfo]]
    ) -> Dict[str, Dict[str, str]]:
        """Create a comparison summary of all routes"""
        comparison = {}
        
        if primary_route:
            comparison[primary_route.transport_mode] = {
                "distance": primary_route.distance,
                "duration": primary_route.duration,
                "mode": primary_route.transport_mode
            }
        
        for mode, route in alternative_routes.items():
            if route:
                comparison[mode] = {
                    "distance": route.distance,
                    "duration": route.duration,
                    "mode": mode
                }
        
        return comparison
    
    def should_process(self, state: TravelState) -> bool:
        """Check if maps processing is needed"""
        return not state.get('maps_complete', False)
    
    async def get_quick_route_info(self, origin: str, destination: str) -> Optional[str]:
        """Get quick route information for API responses"""
        try:
            route = await self.maps_service.get_route_between_locations(
                origin, destination, "driving"
            )
            
            if route:
                return f"{route.distance} journey taking approximately {route.duration} by car"
            else:
                return "Route information unavailable"
                
        except Exception as e:
            self.log_error("Failed to get quick route info", str(e))
            return "Route calculation failed"
    
    def format_route_summary(self, route: RouteInfo) -> str:
        """Format route information for display"""
        if not route:
            return "No route information available"
        
        summary_parts = [
            f"Distance: {route.distance}",
            f"Duration: {route.duration}",
            f"Mode: {route.transport_mode.title()}"
        ]
        
        if route.traffic_info:
            summary_parts.append(f"Traffic: {route.traffic_info}")
        
        return " | ".join(summary_parts)
    
    async def compare_transport_modes(
        self, 
        origin: str, 
        destination: str
    ) -> Dict[str, Dict[str, str]]:
        """Compare different transportation modes for a journey"""
        try:
            routes = await self.maps_service.get_multiple_route_options(origin, destination)
            
            comparison = {}
            for mode, route in routes.items():
                if route:
                    comparison[mode] = {
                        "distance": route.distance,
                        "duration": route.duration,
                        "summary": self.format_route_summary(route)
                    }
                else:
                    comparison[mode] = {
                        "distance": "N/A",
                        "duration": "N/A", 
                        "summary": "Route unavailable"
                    }
            
            return comparison
            
        except Exception as e:
            self.log_error("Failed to compare transport modes", str(e))
            return {}