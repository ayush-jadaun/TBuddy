"""
Worker package for Ringmaster Round Table

This package contains all agent workers that run as independent processes
and communicate via Redis pub/sub.

Available workers:
- weather_worker: Weather forecasting agent
- events_worker: Event discovery agent  
- maps_worker: Route planning agent
- budget_worker: Budget estimation agent
- itinerary_worker: Itinerary generation agent
"""

from app.workers.base_worker import BaseWorker, run_worker

__all__ = [
    'BaseWorker',
    'run_worker'
]