import React, { useState, useEffect } from 'react';

const DriverSelection = ({ onDriverSelect, selectedDriver, isStartingRace }) => {
  const [drivers, setDrivers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch drivers data
  useEffect(() => {
    const fetchDrivers = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/drivers');
        const data = await response.json();
        setDrivers(data.drivers);
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching drivers:', error);
        setIsLoading(false);
      }
    };

    fetchDrivers();
  }, []);

  const handleDriverSelect = (driver) => {
    onDriverSelect(driver);
  };

  if (isLoading || isStartingRace) {
    return (
      <div className="driver-selection">
        <div className="selection-header">
          <h2>Choose Your Driver</h2>
          <p>Select a driver to follow their position changes</p>
        </div>
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>{isStartingRace ? 'Starting race...' : 'Loading drivers...'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="driver-selection">
      <div className="selection-header">
        <h2>Choose Your Driver</h2>
        <p>Select a driver to follow their position changes</p>
      </div>
      
      <div className="drivers-grid">
        {drivers.map((driver) => (
          <button
            key={driver.name}
            className={`driver-card ${selectedDriver?.name === driver.name ? 'selected' : ''}`}
            onClick={() => handleDriverSelect(driver)}
            style={{
              '--team-color': driver.team_color || '#000000'
            }}
          >
            <div className="driver-card-header">
              <div 
                className="team-color-bar" 
                style={{ backgroundColor: driver.team_color || '#000000' }}
              ></div>
              <div className="driver-info">
                <h3>{driver.name}</h3>
                <p>{driver.team}</p>
              </div>
            </div>
            <div className="driver-card-footer">
              <span className="driver-number">#{driver.number}</span>
            </div>
          </button>
        ))}
      </div>
      
      {selectedDriver && (
        <div className="selected-driver-info">
          <p>Following: <strong>{selectedDriver.name}</strong> from {selectedDriver.team}</p>
        </div>
      )}
    </div>
  );
};

export default DriverSelection;
