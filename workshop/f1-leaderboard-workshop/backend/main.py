import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from models import F1_DRIVERS
from kafka_producer import position_producer
from kafka_consumer import kafka_consumer
from race_manager import race_manager

class RaceStartRequest(BaseModel):
    driver_name: str

# Global storage for SSE connections
position_connections = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting F1 Leaderboard API...")
    
    # Start Kafka consumer
    kafka_consumer.start_consuming()
    
    # Add callbacks for SSE updates
    kafka_consumer.add_position_callback(notify_position_connections)
    
    # Set up race manager with position producer
    race_manager.position_producer = position_producer
    
    # Start cleanup task for finished races
    asyncio.create_task(race_manager.start_cleanup_task())
    
    yield
    
    # Shutdown
    print("Shutting down F1 Leaderboard API...")
    position_producer.stop()
    kafka_consumer.stop_consuming()
    race_manager.stop_cleanup_task()

app = FastAPI(title="F1 Leaderboard API", lifespan=lifespan)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def notify_position_connections(positions, race_id=None):
    """Notify all connected clients about position updates"""
    try:
        global position_connections
        if not position_connections:
            return
        
        data = {
            "type": "positions",
            "data": {
                "positions": positions,  # positions is already a list of dicts
                "timestamp": datetime.now().isoformat(),
                "race_id": race_id
            }
        }
        
        message = f"data: {json.dumps(data)}\n\n"
        
        # Send to all connected clients
        disconnected = []
        for connection in list(position_connections):
            try:
                connection.put_nowait(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            if connection in position_connections:
                position_connections.remove(connection)
    except Exception as e:
        print(f"Error in notify_position_connections: {e}")


@app.get("/")
async def root():
    return {"message": "F1 Leaderboard API is running"}

@app.get("/api/drivers")
async def get_drivers():
    """Get list of all F1 drivers"""
    return {"drivers": [driver.dict() for driver in F1_DRIVERS]}

@app.post("/api/race/start")
async def start_race(request: RaceStartRequest):
    """Start a new race for the specified driver"""
    try:
        # Create race
        race_id = race_manager.create_race(request.driver_name)
        
        # Start race simulation in background
        asyncio.create_task(race_manager.start_race_simulation(race_id))
        
        return {
            "race_id": race_id,
            "driver_name": request.driver_name,
            "status": "started",
            "message": f"Race started for {request.driver_name}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start race: {str(e)}")

@app.post("/api/race/{race_id}/stop")
async def stop_race(race_id: str):
    """Stop a running race"""
    try:
        success = race_manager.stop_race(race_id)
        if success:
            return {"message": "Race stopped successfully"}
        else:
            raise HTTPException(status_code=404, detail="Race not found or already stopped")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/race/{race_id}/status")
async def get_race_status(race_id: str):
    """Get status of a specific race"""
    status = race_manager.get_race_status(race_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Race not found")
    return status

@app.get("/api/race/{race_id}/positions")
async def get_race_positions(race_id: str):
    """Get final positions for a finished race"""
    positions = race_manager.get_final_positions(race_id)
    if positions is None:
        raise HTTPException(status_code=404, detail="Race not found or not finished")
    return {"positions": positions}

@app.get("/api/race/{race_id}/avg-speeds")
async def get_race_avg_speeds(race_id: str):
    """Get average speeds for a specific race"""
    avg_speeds = kafka_consumer.get_race_avg_speeds(race_id)
    return {"avg_speeds": avg_speeds or []}

@app.get("/api/positions/stream")
async def stream_positions(race_id: str = Query(None, description="Optional race ID to filter positions")):
    """SSE endpoint for real-time position updates"""
    async def event_generator():
        # Create a queue for this connection
        queue = asyncio.Queue()
        position_connections.append(queue)
        
        try:
            # Send initial positions if available
            latest_positions = kafka_consumer.get_latest_positions(race_id)
            if latest_positions:
                data = {
                    "type": "positions",
                    "data": {
                        "positions": latest_positions,  # positions is already a list of dicts
                        "timestamp": datetime.now().isoformat(),
                        "race_id": race_id
                    }
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # Keep connection alive and send updates
            while True:
                try:
                    # Wait for new data with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield message
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        
        finally:
            # Remove connection when client disconnects
            if queue in position_connections:
                position_connections.remove(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": {
            "positions": len(position_connections)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
