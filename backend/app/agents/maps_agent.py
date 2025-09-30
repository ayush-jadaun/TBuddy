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
        """
    
    async def handle_request(self, request: MCPMessage) -> Dict[str, Any]:
        """
        Handle MCP request for route data
        
        Expected payload:
        {
            "origin": "New Delhi, India",
            "destination": "Agra, India",
            "transport_mode": "driving"  # optional, defaults to "driving"
        }
        
        Returns:
        {
            "primary_route": {...},
            "alternative_routes": {...},
            "route_analysis": "...",
            "recommended_mode": "driving",
            "comparison": {...}
        }
        """
        payload = request.payload
        origin = payload.get("origin")
        destination = payload.get("destination")
        transport_mode = payload.get("transport_mode", "driving")
        
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
            progress_percent=25
        )
        
        # Get primary route
        primary_route = await self.maps_service.get_route_between_locations(
            origin=origin,
            destination=destination,
            transport_mode=transport_mode
        )
        
        if not primary_route:
            # Create fallback route
            primary_route = self._create_fallback_route_info_dict(origin, destination, transport_mode)
        
        # Send progress update
        await self._send_streaming_update(
            request.session_id,
            "progress",
            "Analyzing alternative transportation options",
            progress_percent=50
        )
        
        # Get alternative routes
        alternative_routes = await self._get_alternative_routes_for_request(
            origin, destination, transport_mode
        )
        
        # Send progress update
        await self._send_streaming_update(
            request.session_id,
            "progress",
            "Generating route recommendations",
            progress_percent=75
        )
        
        # Generate route analysis using LLM
        route_analysis = await self._generate_route_insights_for_request(
            primary_route,
            alternative_routes,
            origin,
            destination
        )
        
        # Create comparison data
        comparison = self._create_route_comparison(primary_route, alternative_routes)
        
        self.log_action("Route data retrieved", f"Primary: {transport_mode}, Alternatives: {len(alternative_routes)}")
        
        # Convert RouteInfo to dict if needed
        primary_route_dict = primary_route.dict() if hasattr(primary_route, 'dict') else primary_route
        alternative_routes_dict = {
            mode: (route.dict() if hasattr(route, 'dict') else route)
            for mode, route in alternative_routes.items()
        }
        
        return {
            "primary_route": primary_route_dict,
            "alternative_routes": alternative_routes_dict,
            "route_analysis": route_analysis,
            "recommended_mode": self._determine_recommended_mode(primary_route, alternative_routes),
            "comparison": comparison,
            "origin": origin,
            "destination": destination
        }
    
    async def process(self, state: TravelState) -> TravelState:
        """Legacy method - Process route information for the travel itinerary"""
        self.log_action("Starting route analysis", f"From {state['origin']} to {state['destination']}")
        
        try:
            # Get primary route (driving by default) 
            transport_mode = state.get('preferred_transport', 'driving')
            
            primary_route = await self.maps_service.get_route_between_locations(
                origin=state['origin'],
                destination=state['destination'],
                transport_mode=transport_mode
            )
            
            if primary_route:
                # Store primary route data in state
                state['route_data'] = primary_route
                
                # Get alternative transportation options (but don't fail if they don't work)
                alternative_routes = await self._get_alternative_routes(state)
                
                # Generate route insights using LLM
                route_analysis = await self._generate_route_insights(
                    primary_route, alternative_routes, state
                )
                
                self.add_message_to_state(
                    state, 
                    f"Route analysis complete. {route_analysis}"
                )
                
                self.log_action("Route analysis completed successfully")
            else:
                # Create fallback route information
                fallback_route = self._create_fallback_route_info(state)
                state['route_data'] = fallback_route
                
                self.add_message_to_state(
                    state,
                    f"Basic route information available for {state['origin']} to {state['destination']}"
                )
                
                self.log_action("Used fallback route information")
                
        except Exception as e:
            error_msg = f"Failed to get route information: {str(e)}"
            self.add_error_to_state(state, error_msg)
            
            # Even with errors, try to provide basic route info
            try:
                fallback_route = self._create_fallback_route_info(state)
                state['route_data'] = fallback_route
            except:
                pass  # If even fallback fails, continue without route data
                
        finally:
            state['maps_complete'] = True
            
        return state
    
    def _create_fallback_route_info(self, state: TravelState) -> RouteInfo:
        """Create basic route information when API calls fail (legacy)"""
        return RouteInfo(
            distance="Distance calculation unavailable",
            duration="Duration estimation unavailable",
            steps=[f"Travel from {state['origin']} to {state['destination']}"],
            traffic_info=None,
            transport_mode=state.get('preferred_transport', 'driving')
        )
    
    def _create_fallback_route_info_dict(self, origin: str, destination: str, transport_mode: str) -> Dict[str, Any]:
        """Create basic route information when API calls fail (MCP)"""
        return {
            "distance": "Distance calculation unavailable",
            "duration": "Duration estimation unavailable",
            "steps": [f"Travel from {origin} to {destination}"],
            "traffic_info": None,
            "transport_mode": transport_mode
        }
    
    async def _get_alternative_routes_for_request(
        self,
        origin: str,
        destination: str,
        primary_mode: str
    ) -> Dict[str, Optional[RouteInfo]]:
        """Get alternative transportation routes for MCP request"""
        self.log_action("Fetching alternative transportation options")
        
        # Get all modes except the primary one
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
            
            return alternatives
            
        except Exception as e:
            self.log_error("Failed to get alternative routes", str(e))
            return {}
    
    async def _get_alternative_routes(self, state: TravelState) -> Dict[str, Optional[RouteInfo]]:
        """Get alternative transportation routes (legacy)"""
        self.log_action("Fetching alternative transportation options")
        
        try:
            # Get routes for walking and cycling as alternatives
            tasks = [
                self.maps_service.get_route_between_locations(
                    state['origin'], state['destination'], "walking"
                ),
                self.maps_service.get_route_between_locations(
                    state['origin'], state['destination'], "cycling"
                )
            ]
            
            walking_route, cycling_route = await asyncio.gather(*tasks, return_exceptions=True)
            
            alternatives = {}
            
            if not isinstance(walking_route, Exception) and walking_route:
                alternatives["walking"] = walking_route
            
            if not isinstance(cycling_route, Exception) and cycling_route:
                alternatives["cycling"] = cycling_route
            
            return alternatives
            
        except Exception as e:
            self.log_error("Failed to get alternative routes", str(e))
            return {}
    
    async def _generate_route_insights_for_request(
        self,
        primary_route: Any,
        alternative_routes: Dict[str, Any],
        origin: str,
        destination: str
    ) -> str:
        """Generate route insights for MCP request"""
        route_summary = self._format_routes_for_llm_from_data(primary_route, alternative_routes)
        
        user_input = f"""
        Origin: {origin}
        Destination: {destination}
        
        Route Analysis:
        {route_summary}
        
        Please provide a concise route recommendation and travel analysis for this journey.
        Consider factors like convenience, time efficiency, and practical considerations.
        """
        
        try:
            insights = await self.invoke_llm(self.get_system_prompt(), user_input)
            return insights
        except Exception as e:
            self.log_error("Failed to generate route insights", str(e))
            distance = primary_route.get('distance', 'N/A') if isinstance(primary_route, dict) else getattr(primary_route, 'distance', 'N/A')
            duration = primary_route.get('duration', 'N/A') if isinstance(primary_route, dict) else getattr(primary_route, 'duration', 'N/A')
            mode = primary_route.get('transport_mode', 'driving') if isinstance(primary_route, dict) else getattr(primary_route, 'transport_mode', 'driving')
            return f"Primary route: {distance} in {duration} by {mode}"
    
    async def _generate_route_insights(
        self, 
        primary_route: RouteInfo,
        alternative_routes: Dict[str, Optional[RouteInfo]], 
        state: TravelState
    ) -> str:
        """Generate route insights using the LLM (legacy)"""
        route_summary = self._format_routes_for_llm(primary_route, alternative_routes)
        location_context = self.format_location_context(state)
        
        user_input = f"""
        {location_context}
        
        Route Analysis:
        {route_summary}
        
        Please provide a concise route recommendation and travel analysis for this journey.
        Consider factors like convenience, time efficiency, and practical considerations.
        """
        
        try:
            insights = await self.invoke_llm(self.get_system_prompt(), user_input)
            return insights
        except Exception as e:
            self.log_error("Failed to generate route insights", str(e))
            return f"Primary route: {primary_route.distance} in {primary_route.duration} by {primary_route.transport_mode}"
    
    def _format_routes_for_llm_from_data(
        self,
        primary_route: Any,
        alternative_routes: Dict[str, Any]
    ) -> str:
        """Format route data for LLM consumption (works with dict or RouteInfo)"""
        def get_attr(obj, key, default='N/A'):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        primary_distance = get_attr(primary_route, 'distance')
        primary_duration = get_attr(primary_route, 'duration')
        primary_mode = get_attr(primary_route, 'transport_mode', 'driving')
        primary_steps = get_attr(primary_route, 'steps', [])
        
        formatted_data = [f"""
        PRIMARY ROUTE ({primary_mode.upper()}):
        Distance: {primary_distance}
        Duration: {primary_duration}
        Transport: {primary_mode}
        Key Steps: {'; '.join(primary_steps[:3]) if primary_steps else 'N/A'}
        """]
        
        for mode, route in alternative_routes.items():
            if route:
                alt_distance = get_attr(route, 'distance')
                alt_duration = get_attr(route, 'duration')
                formatted_data.append(f"""
        ALTERNATIVE ({mode.upper()}):
        Distance: {alt_distance}
        Duration: {alt_duration}
        Transport: {mode}
                """)
        
        return "\n".join(formatted_data)
    
    def _format_routes_for_llm(
        self, 
        primary_route: RouteInfo, 
        alternative_routes: Dict[str, Optional[RouteInfo]]
    ) -> str:
        """Format route data for LLM consumption (legacy)"""
        formatted_data = [f"""
        PRIMARY ROUTE (Driving):
        Distance: {primary_route.distance}
        Duration: {primary_route.duration}
        Transport: {primary_route.transport_mode}
        Key Steps: {'; '.join(primary_route.steps[:3])}
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
        primary_route: Any,
        alternative_routes: Dict[str, Any]
    ) -> str:
        """Determine the recommended transportation mode based on route data"""
        # Simple heuristic: recommend primary if available, otherwise first alternative
        if primary_route:
            mode = primary_route.get('transport_mode') if isinstance(primary_route, dict) else getattr(primary_route, 'transport_mode', 'driving')
            return mode
        
        if alternative_routes:
            return list(alternative_routes.keys())[0]
        
        return "driving"
    
    def _create_route_comparison(
        self,
        primary_route: Any,
        alternative_routes: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """Create a comparison summary of all routes"""
        def get_attr(obj, key, default='N/A'):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        comparison = {}
        
        # Add primary route
        primary_mode = get_attr(primary_route, 'transport_mode', 'driving')
        comparison[primary_mode] = {
            "distance": get_attr(primary_route, 'distance'),
            "duration": get_attr(primary_route, 'duration'),
            "mode": primary_mode
        }
        
        # Add alternatives
        for mode, route in alternative_routes.items():
            if route:
                comparison[mode] = {
                    "distance": get_attr(route, 'distance'),
                    "duration": get_attr(route, 'duration'),
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