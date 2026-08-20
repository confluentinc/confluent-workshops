from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class Driver(BaseModel):
    id: int
    name: str
    team: str
    team_color: str

class DriverPosition(BaseModel):
    driver_name: str
    position: int


class RaceStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class Race(BaseModel):
    race_id: str
    selected_driver: Driver
    status: RaceStatus
    start_time: Optional[datetime] = None
    duration: int = 120  # seconds (2 minutes)
    end_time: Optional[datetime] = None
    created_at: datetime = datetime.now()

class LeaderboardUpdate(BaseModel):
    driver_name: str
    position: int
    timestamp: datetime
    race_id: Optional[str] = None

# Hardcoded F1 drivers data
F1_DRIVERS = [
    Driver(id=1, name="Lewis Hamilton", team="Mercedes", team_color="#00D2BE"),
    Driver(id=2, name="Max Verstappen", team="Red Bull Racing", team_color="#1E41FF"),
    Driver(id=3, name="Charles Leclerc", team="Ferrari", team_color="#DC143C"),
    Driver(id=4, name="Carlos Sainz", team="Ferrari", team_color="#DC143C"),
    Driver(id=5, name="Lando Norris", team="McLaren", team_color="#FF8700"),
    Driver(id=6, name="Oscar Piastri", team="McLaren", team_color="#FF8700"),
    Driver(id=7, name="George Russell", team="Mercedes", team_color="#00D2BE"),
    Driver(id=8, name="Fernando Alonso", team="Aston Martin", team_color="#006F62"),
    Driver(id=9, name="Lance Stroll", team="Aston Martin", team_color="#006F62"),
    Driver(id=10, name="Pierre Gasly", team="Alpine", team_color="#FF87BC"),
]
