from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio
import logging
import operator
import uuid

from app.agents.base_agent import AgentType, AgentStatus, StreamingUpdateType
from app.messaging.redis_client import RedisClient, RedisChannels, get_redis_client
from app.config.settings import settings


# ==================== STATE DEFINITION ====================

class OrchestratorState(TypedDict):
    """State for the orchestrator workflow"""
    # Session info
    session_id: str
    user_query: str
    
    # Travel parameters
    destination: Optional[str]
    origin: Optional[str]
    travel_dates: List[str]
    travelers_count: int
    budget_range: Optional[str]
    user_preferences: Optional[Dict[str, Any]]
    needs_itinerary: bool  # NEW: Whether user wants full itinerary
    
    # Workflow control
    agents_to_execute: List[str]
    agent_statuses: Dict[str, str]
    agent_responses: Dict[str, Any]
    
    # Results
    weather_data: Optional[Dict[str, Any]]
    events_data: Optional[Dict[str, Any]]
    maps_data: Optional[Dict[str, Any]]
    budget_data: Optional[Dict[str, Any]]
    itinerary_data: Optional[Dict[str, Any]]
    
    # Metadata
    messages: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    workflow_status: str
    start_time: str
    end_time: Optional[str]


# ==================== ORCHESTRATOR AGENT ====================

class OrchestratorAgent:
    """
    Orchestrator Agent - Coordinates multiple specialized agents using Redis pub/sub
    
    Features:
    - Parses user queries to extract travel parameters
    - Dispatches tasks to specialized agents (weather, events, maps, budget, itinerary)
    - Collects responses asynchronously
    - Streams real-time updates to clients
    - Synthesizes final travel plan (only if requested)
    """
    
    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        gemini_api_key: str = None,
        model_name: str = "gemini-2.5-flash"
    ):
        self.redis_client = redis_client or get_redis_client()
        self.logger = logging.getLogger("orchestrator")
        
        # Initialize Gemini LLM
        api_key = gemini_api_key or getattr(settings, 'google_api_key', None)
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.3,  # Lower temperature for structured extraction
            max_output_tokens=4096
        )
        
        # Build LangGraph workflow
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the orchestrator workflow graph"""
        workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        workflow.add_node("parse_query", self._parse_query_node)
        workflow.add_node("validate_params", self._validate_params_node)
        workflow.add_node("dispatch_agents", self._dispatch_agents_node)
        workflow.add_node("collect_responses", self._collect_responses_node)
        workflow.add_node("synthesize_plan", self._synthesize_plan_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define edges
        workflow.set_entry_point("parse_query")
        workflow.add_edge("parse_query", "validate_params")
        
        # Conditional edge after validation
        workflow.add_conditional_edges(
            "validate_params",
            self._should_continue_after_validation,
            {
                "dispatch": "dispatch_agents",
                "end": "finalize"
            }
        )
        
        workflow.add_edge("dispatch_agents", "collect_responses")
        workflow.add_edge("collect_responses", "synthesize_plan")
        workflow.add_edge("synthesize_plan", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    # ==================== WORKFLOW NODES ====================
    
    async def _parse_query_node(self, state: OrchestratorState) -> OrchestratorState:
        """Parse user query to extract travel parameters using LLM"""
        self.logger.info(f"🔍 Parsing user query for session {state['session_id']}")
        
        await self._send_streaming_update(
            session_id=state["session_id"],
            agent="orchestrator",
            message="Analyzing your travel request...",
            update_type="progress",
            progress_percent=10
        )
        
        user_query = state["user_query"]
        
        # Use LLM to extract structured information
        system_prompt = """
You are a travel query parser. Extract structured information from user travel queries.

Extract the following information:
- destination: The travel destination
- origin: The starting location (if mentioned)
- travel_dates: List of dates in YYYY-MM-DD format (if mentioned)
- travelers_count: Number of travelers
- budget_range: Budget range if mentioned (e.g., "$1000-2000", "moderate", "luxury")
- interests: User interests or preferences (list)
- needs_itinerary: Boolean - Does the user want a complete travel plan/itinerary?

Determine needs_itinerary=true if the query asks for:
- "plan my trip"
- "create an itinerary"
- "full travel plan"
- "what should I do"
- "day by day plan"
- "complete trip planning"
- "help me plan"

Determine needs_itinerary=false if the query only asks for:
- "what's the weather"
- "find events"
- "how do I get there"
- "what's my budget"
- Specific single-aspect questions

Return the information in a structured format:
Destination: <destination>
Origin: <origin or "Not specified">
Travel Dates: <dates or "Not specified">
Travelers Count: <number>
Budget Range: <budget or "Not specified">
Interests: <comma-separated interests or "Not specified">
Needs Itinerary: <true or false>

Be specific and extract only factual information from the query.
"""
        
        user_input = f"Parse this travel query: {user_query}"
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ])
            
            # Parse LLM response
            parsed_data = self._parse_llm_extraction(response.content)
            
            # Update state with parsed data
            state["destination"] = parsed_data.get("destination")
            state["origin"] = parsed_data.get("origin")
            state["travel_dates"] = parsed_data.get("travel_dates", [])
            state["travelers_count"] = parsed_data.get("travelers_count", 1)
            state["budget_range"] = parsed_data.get("budget_range")
            state["needs_itinerary"] = parsed_data.get("needs_itinerary", False)
            
            if parsed_data.get("interests"):
                state["user_preferences"] = {"interests": parsed_data["interests"]}
            
            state["messages"].append(
                f"Query parsed: Destination={state['destination']}, "
                f"Needs itinerary={state['needs_itinerary']}"
            )
            self.logger.info(
                f"✅ Query parsed - Destination: {state['destination']}, "
                f"Needs itinerary: {state['needs_itinerary']}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse query: {str(e)}")
            state["errors"].append(f"Query parsing failed: {str(e)}")
            state["needs_itinerary"] = False  # Default to false on error
        
        return state
    
    def _parse_llm_extraction(self, llm_response: str) -> Dict[str, Any]:
        """Parse the LLM's structured response"""
        result = {
            "destination": None,
            "origin": None,
            "travel_dates": [],
            "travelers_count": 1,
            "budget_range": None,
            "interests": [],
            "needs_itinerary": False
        }
        
        lines = llm_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' not in line:
                continue
            
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if value.lower() in ["not specified", "not mentioned", "none", ""]:
                continue
            
            if "destination" in key:
                result["destination"] = value
            elif "origin" in key:
                result["origin"] = value
            elif "travel dates" in key or "dates" in key:
                # Parse dates from comma-separated string
                dates = [d.strip() for d in value.split(',')]
                result["travel_dates"] = [d for d in dates if d]
            elif "travelers" in key or "count" in key:
                try:
                    result["travelers_count"] = int(value.split()[0])
                except:
                    result["travelers_count"] = 1
            elif "budget" in key:
                result["budget_range"] = value
            elif "interest" in key:
                interests = [i.strip() for i in value.split(',')]
                result["interests"] = [i for i in interests if i]
            elif "needs itinerary" in key or "needs_itinerary" in key:
                result["needs_itinerary"] = value.lower() in ["true", "yes", "1"]
        
        return result
    
    async def _validate_params_node(self, state: OrchestratorState) -> OrchestratorState:
        """Validate extracted parameters"""
        self.logger.info("✔️  Validating travel parameters")
        
        await self._send_streaming_update(
            session_id=state["session_id"],
            agent="orchestrator",
            message="Validating travel parameters...",
            update_type="progress",
            progress_percent=20
        )
        
        errors = []
        
        if not state.get("destination"):
            errors.append("Destination is required")
        
        if not state.get("travel_dates") or len(state["travel_dates"]) == 0:
            errors.append("Travel dates are required")
        
        if errors:
            state["errors"].extend(errors)
            state["workflow_status"] = "validation_failed"
            self.logger.error(f"Validation failed: {errors}")
        else:
            state["workflow_status"] = "validated"
            state["messages"].append("Parameters validated successfully")
            self.logger.info("✅ Parameters validated")
        
        return state
    
    def _should_continue_after_validation(self, state: OrchestratorState) -> str:
        """Decide whether to continue workflow after validation"""
        if state["workflow_status"] == "validated":
            return "dispatch"
        return "end"
    
    async def _dispatch_agents_node(self, state: OrchestratorState) -> OrchestratorState:
        """Dispatch requests to specialized agents"""
        self.logger.info("📤 Dispatching requests to specialized agents")
        
        await self._send_streaming_update(
            session_id=state["session_id"],
            agent="orchestrator",
            message="Dispatching requests to specialized agents...",
            update_type="progress",
            progress_percent=30
        )
        
        session_id = state["session_id"]
        
        # Determine which agents to call
        agents_to_call = ["weather"]  # Always fetch weather
        
        # Add other agents based on available data
        if state.get("destination"):
            agents_to_call.extend(["events", "maps"])
        
        if state.get("budget_range") or state.get("travelers_count"):
            agents_to_call.append("budget")
        
        # NOTE: Itinerary agent is NOT added here
        # It's called separately in synthesize_plan_node ONLY if needs_itinerary=true
        
        state["agents_to_execute"] = agents_to_call
        state["agent_statuses"] = {agent: "pending" for agent in agents_to_call}
        
        # Dispatch requests in parallel
        dispatch_tasks = []
        
        if "weather" in agents_to_call:
            dispatch_tasks.append(self._dispatch_weather(state))
        
        if "events" in agents_to_call:
            dispatch_tasks.append(self._dispatch_events(state))
        
        if "maps" in agents_to_call:
            dispatch_tasks.append(self._dispatch_maps(state))
        
        if "budget" in agents_to_call:
            dispatch_tasks.append(self._dispatch_budget(state))
        
        await asyncio.gather(*dispatch_tasks, return_exceptions=True)
        
        state["messages"].append(f"Dispatched {len(dispatch_tasks)} agent requests")
        self.logger.info(f"✅ Dispatched requests to {len(dispatch_tasks)} agents")
        
        return state
    
    async def _dispatch_weather(self, state: OrchestratorState):
        """Dispatch request to weather agent"""
        request = {
            "request_id": f"weather_{uuid.uuid4().hex[:8]}",
            "session_id": state["session_id"],
            "agent": "weather",
            "action": "request",
            "payload": {
                "destination": state["destination"],
                "travel_dates": state["travel_dates"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        state["agent_statuses"]["weather"] = "processing"
        
        channel = RedisChannels.WEATHER_REQUEST
        await self.redis_client.publish(channel, request)
        
        self.logger.info(f"📡 Dispatched weather request")
    
    async def _dispatch_events(self, state: OrchestratorState):
        """Dispatch request to events agent"""
        interests = None
        if state.get("user_preferences"):
            interests = state["user_preferences"].get("interests")
        
        request = {
            "request_id": f"events_{uuid.uuid4().hex[:8]}",
            "session_id": state["session_id"],
            "agent": "events",
            "action": "request",
            "payload": {
                "destination": state["destination"],
                "travel_dates": state["travel_dates"],
                "interests": interests
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        state["agent_statuses"]["events"] = "processing"
        
        channel = RedisChannels.EVENTS_REQUEST
        await self.redis_client.publish(channel, request)
        
        self.logger.info(f"📡 Dispatched events request")
    
    async def _dispatch_maps(self, state: OrchestratorState):
        """Dispatch request to maps agent"""
        request = {
            "request_id": f"maps_{uuid.uuid4().hex[:8]}",
            "session_id": state["session_id"],
            "agent": "maps",
            "action": "request",
            "payload": {
                "origin": state.get("origin", "Current Location"),
                "destination": state["destination"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        state["agent_statuses"]["maps"] = "processing"
        
        channel = RedisChannels.MAPS_REQUEST
        await self.redis_client.publish(channel, request)
        
        self.logger.info(f"📡 Dispatched maps request")
    
    async def _dispatch_budget(self, state: OrchestratorState):
        """Dispatch request to budget agent"""
        request = {
            "request_id": f"budget_{uuid.uuid4().hex[:8]}",
            "session_id": state["session_id"],
            "agent": "budget",
            "action": "request",
            "payload": {
                "destination": state["destination"],
                "travel_dates": state["travel_dates"],
                "travelers_count": state["travelers_count"],
                "budget_range": state.get("budget_range")
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        state["agent_statuses"]["budget"] = "processing"
        
        channel = RedisChannels.BUDGET_REQUEST
        await self.redis_client.publish(channel, request)
        
        self.logger.info(f"📡 Dispatched budget request")
    
    async def _collect_responses_node(self, state: OrchestratorState) -> OrchestratorState:
        """Collect responses from agents incrementally with streaming"""
        self.logger.info("📥 Collecting responses from agents")
        
        await self._send_streaming_update(
            session_id=state["session_id"],
            agent="orchestrator",
            message="Waiting for agent responses...",
            update_type="progress",
            progress_percent=40
        )
        
        session_id = state["session_id"]
        agents = state["agents_to_execute"]
        
        # Setup response collection
        futures = {agent: asyncio.Future() for agent in agents}
        subscriptions = {}
        
        async def create_handler(agent_name):
            async def handler(data):
                if not futures[agent_name].done():
                    futures[agent_name].set_result(data)
            return handler
        
        # Subscribe to response channels
        for agent in agents:
            channel = RedisChannels.get_response_channel(agent, session_id)
            self.logger.info(f"📡 Subscribed to channel: {channel}")
            subscriptions[agent] = await self.redis_client.subscribe(
                channel,
                await create_handler(agent)
            )
        
        # Collect responses as they arrive
        pending_agents = set(agents)
        completed_count = 0
        total_agents = len(agents)
        
        timeout = 30  # 30 seconds timeout per agent
        
        while pending_agents:
            try:
                done, _ = await asyncio.wait(
                    [futures[agent] for agent in pending_agents],
                    timeout=timeout,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for future in done:
                    agent_name = next(a for a in pending_agents if futures[a] == future)
                    response_data = future.result() if future.done() and not future.exception() else None
                    
                    if response_data:
                        await self._process_agent_response(state, agent_name, response_data)
                        state["agent_statuses"][agent_name] = "completed"
                        completed_count += 1
                        
                        # Stream update about completion
                        progress = 40 + int((completed_count / total_agents) * 40)
                        await self._send_streaming_update(
                            session_id=session_id,
                            agent="orchestrator",
                            message=f"{agent_name.title()} agent completed ({completed_count}/{total_agents})",
                            update_type="progress",
                            progress_percent=progress,
                            data={f"{agent_name}_complete": True}
                        )
                    else:
                        state["agent_statuses"][agent_name] = "timeout"
                        self.logger.warning(f"⏱️ Timeout for {agent_name}")
                    
                    pending_agents.remove(agent_name)
                
            except asyncio.TimeoutError:
                # Timeout for remaining agents
                for agent in pending_agents:
                    state["agent_statuses"][agent] = "timeout"
                    self.logger.warning(f"⏱️ Timeout for {agent}")
                break
        
        # Cleanup subscriptions
        for subscription_id in subscriptions.values():
            await self.redis_client.unsubscribe(subscription_id)
        
        completed = sum(1 for s in state["agent_statuses"].values() if s == "completed")
        state["messages"].append(f"Collected {completed}/{len(agents)} agent responses")
        
        return state
    
    async def _process_agent_response(
        self,
        state: OrchestratorState,
        agent_name: str,
        response_data: Dict[str, Any]
    ):
        """Process individual agent response and update state"""
        success = response_data.get("success", False)
        data = response_data.get("data")
        
        if success and data:
            if agent_name == "weather":
                state["weather_data"] = data
            elif agent_name == "events":
                state["events_data"] = data
            elif agent_name == "maps":
                state["maps_data"] = data
            elif agent_name == "budget":
                state["budget_data"] = data
            elif agent_name == "itinerary":
                state["itinerary_data"] = data
            
            self.logger.info(f"✅ {agent_name} completed successfully")
        else:
            error = response_data.get("error", "Unknown error")
            state["errors"].append(f"{agent_name}: {error}")
            self.logger.error(f"❌ {agent_name} failed: {error}")
    
    async def _synthesize_plan_node(self, state: OrchestratorState) -> OrchestratorState:
        """Synthesize final travel plan from all agent data"""
        self.logger.info("🎨 Synthesizing final travel plan")
        
        # Check if user wants a full itinerary
        if not state.get("needs_itinerary", False):
            self.logger.info("⏭️ Skipping itinerary synthesis - not requested by user")
            state["messages"].append("Skipped itinerary synthesis (user requested specific info only)")
            return state
        
        # User wants full itinerary - proceed with synthesis
        await self._send_streaming_update(
            session_id=state["session_id"],
            agent="orchestrator",
            message="Creating your personalized travel itinerary...",
            update_type="progress",
            progress_percent=85
        )
        
        # Check if we have enough data for itinerary synthesis
        has_required_data = (
            state.get("destination") and 
            state.get("travel_dates") and
            len(state.get("travel_dates", [])) > 0
        )
        
        if has_required_data:
            self.logger.info("📋 Dispatching to itinerary agent for synthesis")
            
            # Dispatch to itinerary agent with all collected data
            await self._dispatch_itinerary(state)
            
            # Wait for itinerary response
            response = await self._wait_for_itinerary_response(state)
            
            if response:
                await self._process_agent_response(state, "itinerary", response)
                state["agent_statuses"]["itinerary"] = "completed"
                state["messages"].append("Itinerary synthesis completed")
                
                # Send streaming update about itinerary completion
                await self._send_streaming_update(
                    session_id=state["session_id"],
                    agent="orchestrator",
                    message="Personalized itinerary created",
                    update_type="progress",
                    progress_percent=95,
                    data={"itinerary_complete": True}
                )
            else:
                state["agent_statuses"]["itinerary"] = "timeout"
                state["errors"].append("Itinerary agent timeout")
                state["messages"].append("Created basic travel summary (itinerary timeout)")
                self.logger.warning("⏱️ Itinerary agent timed out")
        else:
            # Not enough data to create itinerary
            state["messages"].append("Skipped itinerary synthesis (insufficient data)")
            self.logger.warning("⚠️ Insufficient data for itinerary synthesis")
        
        return state
    
    async def _dispatch_itinerary(self, state: OrchestratorState):
        """Dispatch request to itinerary agent for synthesis"""
        request = {
            "request_id": f"itinerary_{uuid.uuid4().hex[:8]}",
            "session_id": state["session_id"],
            "agent": "itinerary",
            "action": "request",
            "payload": {
                "destination": state["destination"],
                "origin": state.get("origin"),
                "travel_dates": state["travel_dates"],
                "travelers_count": state["travelers_count"],
                "budget_range": state.get("budget_range"),
                # Pass all collected agent data
                "weather_data": state.get("weather_data"),
                "events_data": state.get("events_data"),
                "maps_data": state.get("maps_data"),
                "route_data": state.get("maps_data"),  # Alias for compatibility
                "budget_data": state.get("budget_data"),
                "user_preferences": state.get("user_preferences")
            },
            "metadata": {
                "timeout_ms": 45000  # 45 second timeout for synthesis
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        channel = RedisChannels.ITINERARY_REQUEST
        await self.redis_client.publish(channel, request)
        
        self.logger.info(f"📡 Dispatched itinerary synthesis request")
    
    async def _wait_for_itinerary_response(
        self,
        state: OrchestratorState,
        timeout: float = 50.0  # Longer timeout for synthesis
    ) -> Optional[Dict[str, Any]]:
        """Wait for itinerary agent response"""
        session_id = state["session_id"]
        channel = RedisChannels.get_response_channel("itinerary", session_id)
        
        self.logger.info(f"📡 Subscribed to channel: {channel}")
        
        response_future = asyncio.Future()
        
        async def handler(data):
            if not response_future.done():
                self.logger.info(f"📥 Received itinerary response")
                response_future.set_result(data)
        
        subscription_id = await self.redis_client.subscribe(channel, handler)
        
        try:
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            self.logger.warning(f"⏱️ Timeout waiting for itinerary ({timeout}s)")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error waiting for itinerary: {str(e)}")
            return None
        finally:
            await self.redis_client.unsubscribe(subscription_id)
    
    async def _finalize_node(self, state: OrchestratorState) -> OrchestratorState:
        """Finalize workflow and prepare final response"""
        self.logger.info("🎯 Finalizing travel plan")
        
        state["end_time"] = datetime.utcnow().isoformat()
        state["workflow_status"] = "completed"
        
        # Count successful agents
        completed = sum(1 for s in state["agent_statuses"].values() if s == "completed")
        total = len(state["agent_statuses"])
        
        # Send final streaming update
        await self._send_streaming_update(
            session_id=state["session_id"],
            agent="orchestrator",
            message=f"Travel plan completed! ({completed}/{total} agents successful)",
            update_type="completed",
            progress_percent=100,
            data={
                "weather_data": state.get("weather_data"),
                "events_data": state.get("events_data"),
                "maps_data": state.get("maps_data"),
                "budget_data": state.get("budget_data"),
                "itinerary_data": state.get("itinerary_data")
            }
        )
        
        state["messages"].append(f"Workflow completed with {completed}/{total} agents")
        
        # Save final state to Redis
        await self.redis_client.set_state(
            state["session_id"],
            dict(state),
            ttl=7200  # 2 hours
        )
        
        self.logger.info(f"🎉 Workflow completed successfully")
        
        return state
    
    # ==================== STREAMING ====================
    
    async def _send_streaming_update(
        self,
        session_id: str,
        agent: str,
        message: str,
        update_type: str,
        progress_percent: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send streaming update via Redis"""
        try:
            update = {
                "session_id": session_id,
                "agent": agent,
                "type": update_type,
                "message": message,
                "progress_percent": progress_percent,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            channel = RedisChannels.get_streaming_channel(session_id)
            await self.redis_client.publish(channel, update)
            
        except Exception as e:
            self.logger.warning(f"Failed to send streaming update: {str(e)}")
    
    # ==================== PUBLIC API ====================
    
    async def process_query(self, user_query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user travel query
        
        Args:
            user_query: Natural language travel query from user
            session_id: Optional session ID for tracking
            
        Returns:
            Final travel plan with all agent responses
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        # Connect to Redis
        await self.redis_client.connect()
        
        # Create initial state
        initial_state = {
            "session_id": session_id,
            "user_query": user_query,
            "destination": None,
            "origin": None,
            "travel_dates": [],
            "travelers_count": 1,
            "budget_range": None,
            "user_preferences": None,
            "needs_itinerary": False,
            "agents_to_execute": [],
            "agent_statuses": {},
            "agent_responses": {},
            "weather_data": None,
            "events_data": None,
            "maps_data": None,
            "budget_data": None,
            "itinerary_data": None,
            "messages": [],
            "errors": [],
            "workflow_status": "initialized",
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None
        }
        
        self.logger.info(
            f"🎪 Starting orchestration workflow\n"
            f"   Session: {session_id}\n"
            f"   Query: {user_query}"
        )
        
        try:
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                "session_id": session_id,
                "status": final_state["workflow_status"],
                "destination": final_state.get("destination"),
                "travel_dates": final_state.get("travel_dates"),
                "needs_itinerary": final_state.get("needs_itinerary"),
                "weather": final_state.get("weather_data"),
                "events": final_state.get("events_data"),
                "maps": final_state.get("maps_data"),
                "budget": final_state.get("budget_data"),
                "itinerary": final_state.get("itinerary_data"),
                "messages": final_state["messages"],
                "errors": final_state["errors"],
                "agent_statuses": final_state["agent_statuses"]
            }
            
        except Exception as e:
            self.logger.error(f"Orchestration failed: {str(e)}", exc_info=True)
            raise


# ==================== HELPER FUNCTIONS ====================

async def create_orchestrator(
    redis_client: Optional[RedisClient] = None,
    gemini_api_key: Optional[str] = None
) -> OrchestratorAgent:
    """
    Create and initialize an orchestrator agent
    
    Args:
        redis_client: Optional Redis client instance
        gemini_api_key: Optional Gemini API key
        
    Returns:
        Initialized OrchestratorAgent
    """
    orchestrator = OrchestratorAgent(
        redis_client=redis_client,
        gemini_api_key=gemini_api_key
    )
    
    # Connect Redis if not already connected
    if orchestrator.redis_client:
        await orchestrator.redis_client.connect()
    
    return orchestrator


# ==================== STANDALONE RUNNER ====================

async def run_orchestrator_standalone():
    """Run the orchestrator as a standalone service for testing"""
    from app.messaging.redis_client import get_redis_client
    from app.config.settings import settings
    
    # Get Redis client
    redis_client = get_redis_client()
    await redis_client.connect()
    
    # Create orchestrator
    orchestrator = OrchestratorAgent(
        redis_client=redis_client,
        gemini_api_key=settings.google_api_key
    )
    
    print("🎪 Orchestrator Agent is ready!")
    print("\nExample queries:")
    print("  1. 'Plan my trip to Paris from Dec 15-20'")
    print("  2. 'What's the weather in Tokyo next week?'")
    print("  3. 'Find events in New York this weekend'")
    print("  4. 'Create a complete itinerary for London, 3 days'")
    print("\nEnter a query (or 'quit' to exit):\n")
    
    try:
        while True:
            user_input = input("> ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input.strip():
                continue
            
            print("\n🔄 Processing...\n")
            
            try:
                result = await orchestrator.process_query(user_input)
                
                print(f"\n✅ Status: {result['status']}")
                print(f"📍 Destination: {result.get('destination')}")
                print(f"📅 Travel Dates: {result.get('travel_dates')}")
                print(f"📋 Needs Itinerary: {result.get('needs_itinerary')}")
                print(f"\n🤖 Agent Statuses:")
                for agent, status in result['agent_statuses'].items():
                    emoji = "✅" if status == "completed" else "⏱️" if status == "timeout" else "❌"
                    print(f"   {emoji} {agent}: {status}")
                
                if result.get('itinerary'):
                    print(f"\n📖 Itinerary created: {result['itinerary'].get('total_days')} days")
                
                if result.get('errors'):
                    print(f"\n⚠️ Errors: {result['errors']}")
                
                print("\n" + "="*60 + "\n")
                
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down orchestrator...")
    
    finally:
        await redis_client.disconnect()
        print("✅ Orchestrator stopped")


if __name__ == "__main__":
    import asyncio
    
    asyncio.run(run_orchestrator_standalone())