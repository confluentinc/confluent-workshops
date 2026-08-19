import React, { useState, useEffect } from 'react';

const AverageSpeedPanel = ({ raceId, selectedDriver }) => {
  const [avgSpeeds, setAvgSpeeds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAvgSpeeds = async () => {
    if (!raceId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8001/api/race/${raceId}/avg-speeds`);
      if (response.ok) {
        const data = await response.json();
        // Filter to only show data for the current race ID
        const filteredSpeeds = (data.avg_speeds || []).filter(speed => speed.race_id === raceId);
        setAvgSpeeds(filteredSpeeds);
      } else {
        setError('Failed to fetch average speeds');
      }
    } catch (err) {
      setError('Error fetching average speeds');
      console.error('Error fetching average speeds:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch average speeds when raceId changes
  useEffect(() => {
    fetchAvgSpeeds();
    
    // Poll for updates every 1 second for low latency
    const interval = setInterval(fetchAvgSpeeds, 1000);
    return () => clearInterval(interval);
  }, [raceId]);

  const getSpeedColor = (speed) => {
    if (speed >= 320) return 'text-green-400';
    if (speed >= 310) return 'text-yellow-400';
    if (speed >= 300) return 'text-orange-400';
    return 'text-red-400';
  };

  const getSpeedBarWidth = (speed) => {
    // Normalize speed to percentage (assuming range 280-330 km/h)
    const minSpeed = 280;
    const maxSpeed = 330;
    const normalized = Math.max(0, Math.min(100, ((speed - minSpeed) / (maxSpeed - minSpeed)) * 100));
    return `${normalized}%`;
  };

  return (
    <div className="avg-speed-panel">
      <div className="avg-speed-header">
        <h3>
          <svg className="w-5 h-5 mr-2 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd"></path>
          </svg>
          Average Speeds
        </h3>
        <button 
          onClick={fetchAvgSpeeds}
          disabled={loading}
          className="refresh-button"
        >
          {loading ? '⏳' : '🔄'}
        </button>
      </div>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="avg-speed-content">
        {avgSpeeds.length === 0 ? (
          <div className="no-data">
            <p>No average speed data available yet</p>
            <small>Data will appear as the race progresses</small>
          </div>
        ) : (
          <div className="speed-list">
            {avgSpeeds.map((driver, index) => {
              const isSelectedDriver = selectedDriver && driver.driver_name === selectedDriver.name;
              
              return (
                <div 
                  key={driver.driver_name} 
                  className={`speed-item ${isSelectedDriver ? 'selected-driver' : ''}`}
                >
                  <div className="speed-info">
                    <div className="driver-name">
                      {driver.driver_name}
                      {isSelectedDriver && <span className="selected-badge">YOU</span>}
                    </div>
                    <div className="team-name">{driver.team_name || 'Unknown Team'}</div>
                  </div>
                  
                  <div className="speed-display">
                    <div className="speed-value">
                      <span className={`speed-number ${getSpeedColor(driver.average_speed)}`}>
                        {driver.average_speed.toFixed(1)}
                      </span>
                      <span className="speed-unit">km/h</span>
                    </div>
                    
                    <div className="speed-bar-container">
                      <div 
                        className="speed-bar"
                        style={{ width: getSpeedBarWidth(driver.average_speed) }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default AverageSpeedPanel;
