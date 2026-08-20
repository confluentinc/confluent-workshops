import React, { useState, useEffect } from 'react';
import { useEventSource } from '../hooks/useEventSource';
import { useDriverPositions } from '../hooks/useDriverPositions';
import DriverRow from './DriverRow';

const Leaderboard = ({ selectedDriver, raceId, raceStatus }) => {
  const [drivers, setDrivers] = useState([]);
  const [previousPositions, setPreviousPositions] = useState([]);
  const { data: positionsData, error: positionsError, isConnected: positionsConnected } = useEventSource('http://localhost:8001/api/positions/stream', { raceId });
  const { driverPositions, highlightedDrivers } = useDriverPositions(positionsData);

  // Fetch initial drivers data
  useEffect(() => {
    const fetchDrivers = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/drivers');
        const data = await response.json();
        setDrivers(data.drivers);
      } catch (error) {
        console.error('Error fetching drivers:', error);
      }
    };

    fetchDrivers();
  }, []);

  // Update previous positions when new data arrives
  useEffect(() => {
    if (driverPositions.length > 0) {
      setPreviousPositions(prev => {
        const current = driverPositions.map(pos => ({
          driver_name: pos.driver_name,
          position: pos.position
        }));
        return prev.length > 0 ? prev : current;
      });
    }
  }, [driverPositions]);

  // Create sorted leaderboard with driver info
  const leaderboard = driverPositions
    .map(pos => {
      const driver = drivers.find(d => d.name === pos.driver_name);
      const previousPos = previousPositions.find(p => p.driver_name === pos.driver_name);
      const isSelectedDriver = selectedDriver && selectedDriver.name === pos.driver_name;
      return {
        ...pos,
        driver: driver,
        teamColor: driver?.team_color || '#000000',
        previousPosition: previousPos?.position,
        isSelectedDriver: isSelectedDriver
      };
    })
    .sort((a, b) => a.position - b.position);


  return (
    <div className="leaderboard-container">
      <div className="leaderboard-header">
        <h2>
          <svg className="w-5 h-5 mr-2 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clipRule="evenodd"></path>
          </svg>
          Live Leaderboard
          {selectedDriver && (
            <span className="selected-driver-badge">
              Following: {selectedDriver.name}
            </span>
          )}
        </h2>
        <div className="connection-status">
          <span className={`status-indicator ${positionsConnected ? 'connected' : 'disconnected'}`}>
            {positionsConnected ? '● Live' : '● Offline'}
          </span>
        </div>
      </div>
      
      {positionsError && (
        <div className="error-message">
          {positionsError}
        </div>
      )}

      <div className="leaderboard-table-container">
        {leaderboard.length === 0 ? (
          <div className="no-data-message">
            <p>No position data available yet</p>
            <small>Waiting for race data...</small>
          </div>
        ) : (
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Driver</th>
                <th className="hidden sm:table-cell">Team</th>
                <th>Speed</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((entry) => (
                <DriverRow
                  key={entry.driver_name}
                  driver={entry.driver}
                  position={entry.position}
                  speed={entry.speed}
                  isHighlighted={entry.isSelectedDriver && highlightedDrivers.has(entry.driver_name)}
                  isSelectedDriver={entry.isSelectedDriver}
                  teamColor={entry.teamColor}
                  previousPosition={entry.previousPosition}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Leaderboard;
