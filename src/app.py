"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings  # Change this line to use relative import

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Initial activities data for database population
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    # Artistic activities
    "Drama Club": {
        "description": "Acting, stage production, and theater performances",
        "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Art Workshop": {
        "description": "Painting, drawing, and creative art projects",
        "schedule": "Mondays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": ["ava@mergington.edu", "liam@mergington.edu"]
    },
    # Intellectual activities
    "Math Club": {
        "description": "Problem solving, math competitions, and logic games",
        "schedule": "Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 16,
        "participants": ["noah@mergington.edu", "isabella@mergington.edu"]
    },
    "Science Olympiad": {
        "description": "Hands-on science experiments and competitions",
        "schedule": "Tuesdays, 4:00 PM - 5:30 PM",
        "max_participants": 14,
        "participants": ["ethan@mergington.edu", "charlotte@mergington.edu"]
    },
    # Related activity
    "Robotics Club": {
        "description": "Design, build, and program robots for competitions",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 10,
        "participants": ["jack@mergington.edu", "amelia@mergington.edu"]
    }
}

# MongoDB connection
client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.db_name]
activities_collection = db.activities


@app.on_event("startup")
async def startup_db_client():
    try:
        # Check if collection is empty
        count = await activities_collection.count_documents({})
        if count == 0:
            # Pre-populate with initial activities
            for name, details in initial_activities.items():
                await activities_collection.insert_one({"_id": name, **details})
    except Exception as e:
        print(f"Error initializing database: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
async def get_activities():
    cursor = activities_collection.find({})
    activities = {}
    async for doc in cursor:
        name = doc.pop('_id')
        activities[name] = doc
    return activities


@app.post("/activities/{activity_name}/signup")
async def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Get the activity
    activity = await activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up")

    # Add student to participants
    result = await activities_collection.update_one(
        {"_id": activity_name},
        {"$push": {"participants": email}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update activity")

    return {"message": f"Signed up {email} for {activity_name}"}
