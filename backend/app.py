"""
### FastAPI Backend for Vacation Planner - Deployable on AWS Bedrock AgentCore / ECS
"""
import os
import sys
import ssl
import urllib3

# Patch ssl FIRST before any other imports
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Monkey-patch httpx to skip SSL verification at import time
try:
    import httpx._config as _httpx_config
    def _patched_ssl(*args, **kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    _httpx_config.create_ssl_context = _patched_ssl
except Exception:
    pass

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json

# Don't import VacationPlanner here - it will be lazy loaded to allow SSL patches to work

app = FastAPI(
    title="Vacation Planner API",
    description="AI-powered vacation planning API using CrewAI and AWS Bedrock",
    version="1.0.0",
    root_path="/api"
)

# CORS - allow React frontend from any origin
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


class PlanRequest(BaseModel):
    source_city: str
    destination: str
    number_of_days: int = 5


class PlanResponse(BaseModel):
    destination: str
    source_city: str
    number_of_days: int
    report: Optional[str] = None
    weather: Optional[str] = None
    itinerary: Optional[str] = None
    hotels: Optional[str] = None
    restaurants: Optional[str] = None
    activities: Optional[str] = None


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "vacation-planner-api"}


@app.post("/plan", response_model=PlanResponse)
def create_plan(request: PlanRequest):
    """Run the full vacation planning crew and return all results."""
    try:
        # Lazy import VacationPlanner here to ensure SSL patches are applied first
        from vacation_planner.crew import VacationPlanner
        
        inputs = {
            "topic": request.destination,
            "source_city": request.source_city,
            "current_year": str(datetime.now().year),
            "number_of_days": str(request.number_of_days)
        }

        result = VacationPlanner().crew().kickoff(inputs=inputs)

        response_data = {
            "destination": request.destination,
            "source_city": request.source_city,
            "number_of_days": request.number_of_days,
        }

        if os.path.exists("/tmp/report.md"):
            with open("/tmp/report.md", "r", encoding="utf-8") as f:
                response_data["report"] = f.read()

        if hasattr(result, 'tasks_output') and len(result.tasks_output) > 2:
            response_data["weather"] = result.tasks_output[2].raw

        if os.path.exists("/tmp/detailed_itinerary.md"):
            with open("/tmp/detailed_itinerary.md", "r", encoding="utf-8") as f:
                response_data["itinerary"] = f.read()

        if os.path.exists("/tmp/hotels.md"):
            with open("/tmp/hotels.md", "r", encoding="utf-8") as f:
                response_data["hotels"] = f.read()

        if os.path.exists("/tmp/restaurants.md"):
            with open("/tmp/restaurants.md", "r", encoding="utf-8") as f:
                response_data["restaurants"] = f.read()

        if os.path.exists("/tmp/activities.md"):
            with open("/tmp/activities.md", "r", encoding="utf-8") as f:
                response_data["activities"] = f.read()

        return PlanResponse(**response_data)

    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


@app.get("/cities")
def get_cities():
    """Return the list of supported cities for autocomplete."""
    cities = [
        "Abu Dhabi", "Accra", "Addis Ababa", "Adelaide", "Agra", "Ahmedabad", "Alexandria",
        "Algiers", "Amman", "Amsterdam", "Anchorage", "Ankara", "Antalya", "Antwerp", "Athens",
        "Atlanta", "Auckland", "Austin", "Baghdad", "Baku", "Bali", "Baltimore", "Bangalore",
        "Bangkok", "Barcelona", "Basel", "Beijing", "Beirut", "Belfast", "Belgrade", "Bergen",
        "Berlin", "Bern", "Bogota", "Bologna", "Boston", "Brasilia", "Bratislava", "Brisbane",
        "Brussels", "Bucharest", "Budapest", "Buenos Aires", "Cairo", "Calgary", "Cancun",
        "Cape Town", "Caracas", "Chennai", "Chicago", "Colombo", "Copenhagen", "Dallas",
        "Delhi", "Denver", "Detroit", "Dhaka", "Doha", "Dubai", "Dublin", "Dubrovnik",
        "Edinburgh", "Florence", "Frankfurt", "Geneva", "Goa", "Hamburg", "Hanoi", "Helsinki",
        "Ho Chi Minh City", "Hong Kong", "Honolulu", "Houston", "Hyderabad", "Istanbul",
        "Jaipur", "Jakarta", "Jerusalem", "Johannesburg", "Karachi", "Kathmandu", "Kochi",
        "Kolkata", "Krakow", "Kuala Lumpur", "Kyoto", "Lagos", "Las Vegas", "Lisbon",
        "Liverpool", "London", "Los Angeles", "Madrid", "Male", "Manchester", "Manila",
        "Marrakech", "Melbourne", "Mexico City", "Miami", "Milan", "Montreal", "Moscow",
        "Mumbai", "Munich", "Nairobi", "Nashville", "New Orleans", "New York", "Nice",
        "Orlando", "Osaka", "Oslo", "Paris", "Perth", "Philadelphia", "Phuket", "Portland",
        "Porto", "Prague", "Pune", "Queenstown", "Reykjavik", "Rio de Janeiro", "Rome",
        "San Diego", "San Francisco", "Santiago", "Sao Paulo", "Seattle", "Seoul", "Shanghai",
        "Singapore", "Stockholm", "Sydney", "Taipei", "Tel Aviv", "Tokyo", "Toronto",
        "Vancouver", "Venice", "Vienna", "Warsaw", "Washington DC", "Wellington", "Zurich"
    ]
    return {"cities": cities}
