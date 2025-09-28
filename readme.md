# 🎪 The Ringmaster's Round Table - Project Structure

```
ringmaster-round-table/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # Environment variables & config
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # Grand Orchestrator (LangGraph)
│   │   └── state.py                # Shared state models
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Base agent class
│   │   ├── weather_agent.py        # Sky Gazer
│   │   ├── maps_agent.py           # Trailblazer
│   │   ├── budget_agent.py         # Quartermaster
│   │   └── itinerary_agent.py      # Itinerary Weaver
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py             # Pydantic request models
│   │   └── responses.py            # Pydantic response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── weather_service.py      # Weather API integration
│   │   └── maps_service.py         # Maps API integration
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py              # Utility functions
│   └── api/
│       ├── __init__.py
│       └── routes.py               # API endpoints
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (not in repo)
├── .env.example                   # Example environment file
├── .gitignore
├── README.md
└── docker-compose.yml             # For easy development setup
```

## Key Components

### 🎭 Core Architecture
- **Grand Orchestrator** (`core/orchestrator.py`): LangGraph-based workflow coordinator
- **Agents** (`agents/`): Individual expert agents with specialized capabilities
- **State Management** (`core/state.py`): Shared state between agents
- **Services** (`services/`): External API integrations

### 🛠 Technology Stack
- **FastAPI**: Modern, fast web framework
- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: Agent framework and tooling
- **Gemini 2.5 Pro**: Primary language model
- **Pydantic**: Data validation and serialization

### 📁 Organization Principles
- **Separation of Concerns**: Clear boundaries between API, business logic, and data
- **Agent Modularity**: Each agent is self-contained and reusable
- **Configuration Management**: Centralized settings and environment handling
- **Service Layer**: Clean abstraction for external integrations