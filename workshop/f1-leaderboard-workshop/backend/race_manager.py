import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum
from models import Driver, F1_DRIVERS
from position_generator import RealisticPositionGenerator

class RaceStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class Race:
    def __init__(self, race_id: str, selected_driver: Driver, position_generator, duration: int = 120):
        self.race_id = race_id
        self.selected_driver = selected_driver
        self.status = RaceStatus.NOT_STARTED
        self.start_time: Optional[datetime] = None
        self.duration = duration  # seconds
        self.end_time: Optional[datetime] = None
        self.created_at = datetime.now()
        self.final_positions: Optional[List[Dict]] = None
        self.position_generator = position_generator
        
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds since race start."""
        if self.start_time is None:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def progress(self) -> float:
        """Get race progress from 0.0 to 1.0."""
        if self.status == RaceStatus.NOT_STARTED:
            return 0.0
        elif self.status == RaceStatus.FINISHED:
            return 1.0
        else:
            return min(1.0, self.elapsed_time / self.duration)
    
    def start(self):
        """Start the race."""
        self.status = RaceStatus.IN_PROGRESS
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=self.duration)
    
    def finish(self):
        """Finish the race."""
        self.status = RaceStatus.FINISHED
        if self.end_time is None:
            self.end_time = datetime.now()
        
        # Generate and store final positions
        if self.final_positions is None:
            self.final_positions = self._generate_final_positions()
    
    def _generate_final_positions(self) -> List[Dict]:
        """Generate final positions for all drivers."""
        # Generate final positions with 100% progress
        positions = self.position_generator.generate_race_positions(
            self.selected_driver.name,
            1.0  # 100% progress for final positions
        )
        
        # Sort by position and add race_id
        positions.sort(key=lambda x: x['position'])
        for position in positions:
            position['race_id'] = self.race_id
            
        return positions
    
    def is_finished(self) -> bool:
        """Check if race should be finished based on time."""
        if self.status == RaceStatus.FINISHED:
            return True
        return self.elapsed_time >= self.duration

class RaceManager:
    def __init__(self, position_producer=None):
        self.races: Dict[str, Race] = {}
        self.position_generator = RealisticPositionGenerator()
        self.position_producer = position_producer
        self.running = False
        self._cleanup_task = None
        
    def create_race(self, driver_name: str) -> str:
        """
        Create a new race for the specified driver.
        
        Args:
            driver_name: Name of the driver to focus on
            
        Returns:
            race_id: Unique identifier for the race
        """
        # Find the driver
        selected_driver = None
        for driver in F1_DRIVERS:
            if driver.name == driver_name:
                selected_driver = driver
                break
        
        if selected_driver is None:
            raise ValueError(f"Driver '{driver_name}' not found")
        
        # Generate unique race ID
        race_id = str(uuid.uuid4())
        
        # Create race
        race = Race(race_id, selected_driver, self.position_generator)
        self.races[race_id] = race
        
        # Reset position generator for this driver
        self.position_generator.reset_race(driver_name)
        
        print(f"Created race {race_id} for driver {driver_name}")
        return race_id
    
    def start_race(self, race_id: str) -> bool:
        """
        Start a race.
        
        Args:
            race_id: ID of the race to start
            
        Returns:
            True if race started successfully, False otherwise
        """
        if race_id not in self.races:
            return False
        
        race = self.races[race_id]
        if race.status != RaceStatus.NOT_STARTED:
            return False
        
        race.start()
        print(f"Started race {race_id}")
        return True
    
    def get_race(self, race_id: str) -> Optional[Race]:
        """Get race by ID."""
        return self.races.get(race_id)
    
    def get_race_status(self, race_id: str) -> Optional[Dict]:
        """
        Get race status information.
        
        Returns:
            Dictionary with race status, progress, elapsed time, etc.
        """
        race = self.get_race(race_id)
        if race is None:
            return None
        
        return {
            "race_id": race.race_id,
            "selected_driver": {
                "name": race.selected_driver.name,
                "team": race.selected_driver.team
            },
            "status": race.status.value,
            "progress": race.progress,
            "elapsed_time": race.elapsed_time,
            "duration": race.duration,
            "remaining_time": max(0, race.duration - race.elapsed_time),
            "start_time": race.start_time.isoformat() if race.start_time else None,
            "end_time": race.end_time.isoformat() if race.end_time else None
        }
    
    def generate_positions_for_race(self, race_id: str) -> Optional[List[Dict]]:
        """
        Generate position updates for a specific race.
        
        Args:
            race_id: ID of the race
            
        Returns:
            List of position updates or None if race not found
        """
        race = self.get_race(race_id)
        if race is None or race.status != RaceStatus.IN_PROGRESS:
            return None
        
        # Check if race should be finished
        if race.is_finished():
            race.finish()
            return None
        
        # Generate positions
        positions = self.position_generator.generate_race_positions(
            race.selected_driver.name,
            race.progress
        )
        
        # Add race_id to each position
        for position in positions:
            position['race_id'] = race_id
        
        return positions
    
    def get_final_positions(self, race_id: str) -> Optional[List[Dict]]:
        """
        Get final positions for a finished race.
        
        Args:
            race_id: ID of the race
            
        Returns:
            List of final positions or None if race not found or not finished
        """
        race = self.get_race(race_id)
        if race is None or race.status != RaceStatus.FINISHED:
            return None
        
        # Try to get the actual latest positions from Kafka consumer first
        try:
            from kafka_consumer import kafka_consumer
            if hasattr(kafka_consumer, 'race_positions') and race_id in kafka_consumer.race_positions:
                latest_positions = kafka_consumer.race_positions[race_id]
                if latest_positions:
                    # Sort by position to ensure correct order
                    sorted_positions = sorted(latest_positions, key=lambda x: x['position'])
                    
                    # Validate that we have exactly 10 drivers and positions 1-10
                    if len(sorted_positions) == 10 and all(1 <= p['position'] <= 10 for p in sorted_positions):
                        positions_str = [f"{p['driver_name']}: P{p['position']}" for p in sorted_positions]
                        print(f"Using actual latest positions for race {race_id}: {positions_str}")
                        return sorted_positions
                    else:
                        print(f"Invalid position data for race {race_id}, falling back to generated positions")
        except Exception as e:
            print(f"Error getting latest positions from Kafka consumer: {e}")
        
        # Fallback to generated positions if no actual data available
        if race.final_positions is None:
            race.final_positions = self._generate_final_positions()
        
        return race.final_positions
    
    async def start_race_simulation(self, race_id: str):
        """
        Start the race simulation loop for a specific race.
        This runs in the background and produces position updates.
        """
        race = self.get_race(race_id)
        if race is None:
            return
        
        # Start the race
        self.start_race(race_id)
        
        # Start position production loop
        while race.status == RaceStatus.IN_PROGRESS:
            try:
                positions = self.generate_positions_for_race(race_id)
                
                if positions is None:
                    # Race finished
                    break
                
                # Produce positions to Kafka if producer is available
                if self.position_producer:
                    await self.position_producer.produce_race_positions(race_id, positions)
                
                # Wait 1 second before next update
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error in race simulation for {race_id}: {e}")
                await asyncio.sleep(1)
        
        # Ensure race is marked as finished if it's not already
        if race.status != RaceStatus.FINISHED:
            race.finish()
        
        print(f"Race {race_id} finished")
    
    def stop_race(self, race_id: str) -> bool:
        """Stop a running race"""
        if race_id not in self.races:
            return False
        
        race = self.races[race_id]
        if race.status == RaceStatus.IN_PROGRESS:
            race.finish()
            print(f"Race {race_id} stopped by user")
            return True
        elif race.status == RaceStatus.FINISHED:
            print(f"Race {race_id} was already finished")
            return True
        else:
            print(f"Race {race_id} was not running")
            return False
    
    def cleanup_finished_races(self):
        """Remove finished races older than 1 hour."""
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        races_to_remove = []
        for race_id, race in self.races.items():
            if (race.status == RaceStatus.FINISHED and 
                race.end_time and 
                race.end_time < cutoff_time):
                races_to_remove.append(race_id)
        
        for race_id in races_to_remove:
            del self.races[race_id]
            print(f"Cleaned up finished race {race_id}")
    
    async def start_cleanup_task(self):
        """Start the cleanup task that runs every 10 minutes."""
        self.running = True
        while self.running:
            try:
                self.cleanup_finished_races()
                await asyncio.sleep(600)  # 10 minutes
            except Exception as e:
                print(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def stop_cleanup_task(self):
        """Stop the cleanup task."""
        self.running = False

# Global race manager instance
race_manager = RaceManager()
