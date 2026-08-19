import React, { useState, useEffect } from 'react';
import Leaderboard from './components/Leaderboard';
import DriverSelection from './components/DriverSelection';
import AverageSpeedPanel from './components/AverageSpeedPanel';
import './App.css';

function App() {
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [raceId, setRaceId] = useState(null);
  const [raceStatus, setRaceStatus] = useState(null);
  const [showMainApp, setShowMainApp] = useState(false);
  const [isStartingRace, setIsStartingRace] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isRaceFinished, setIsRaceFinished] = useState(false);
  const [showRaceStarting, setShowRaceStarting] = useState(false);
  const [showRaceFinished, setShowRaceFinished] = useState(false);
  const [finalPositions, setFinalPositions] = useState(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Poll race status when race is active
  useEffect(() => {
    if (!raceId || isRaceFinished) return;

    const pollRaceStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8001/api/race/${raceId}/status`);
        if (response.ok) {
          const status = await response.json();
          setRaceStatus(status);
          
          // If race is finished, stop polling immediately
          if (status.status === 'finished') {
            setIsRaceFinished(true);
            
            // Fetch final positions but don't show race finished animation yet
            fetchFinalPositions();
          }
        }
      } catch (error) {
        console.error('Error polling race status:', error);
      }
    };

    const interval = setInterval(pollRaceStatus, 1000);
    return () => clearInterval(interval);
  }, [raceId, isRaceFinished]);

  const fetchFinalPositions = async () => {
    try {
      // Add a small delay to ensure we get the latest position data
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const response = await fetch(`http://localhost:8001/api/race/${raceId}/positions`);
      if (response.ok) {
        const data = await response.json();
        setFinalPositions(data.positions || data);
        
        // Show race finished animation immediately
        setShowRaceFinished(true);
      } else {
        console.error('Failed to fetch final positions:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching final positions:', error);
    }
  };

  const handleDriverSelect = async (driver) => {
    setIsStartingRace(true);
    setShowRaceStarting(true);
    
    try {
      // Start a new race
      const response = await fetch('http://localhost:8001/api/race/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ driver_name: driver.name }),
      });

      if (response.ok) {
        const raceData = await response.json();
        setSelectedDriver(driver);
        setRaceId(raceData.race_id);
        
        // Show race starting animation for 3 seconds, then show main app
        setTimeout(() => {
          setShowRaceStarting(false);
          setShowMainApp(true);
        }, 3000);
      } else {
        console.error('Failed to start race');
        setShowRaceStarting(false);
      }
    } catch (error) {
      console.error('Error starting race:', error);
      setShowRaceStarting(false);
    } finally {
      setIsStartingRace(false);
    }
  };


  const handleBackToSelection = () => {
    setShowMainApp(false);
    setSelectedDriver(null);
    setRaceId(null);
    setRaceStatus(null);
    setIsRaceFinished(false);
    setShowRaceStarting(false);
    setShowRaceFinished(false);
    setFinalPositions(null);
  };

  const handleStopRace = async () => {
    if (!raceId) return;
    
    try {
      const response = await fetch(`http://localhost:8001/api/race/${raceId}/stop`, {
        method: 'POST',
      });
      
      if (response.ok) {
        // Race stopped successfully
      } else {
        console.error('Failed to stop race');
      }
    } catch (error) {
      console.error('Error stopping race:', error);
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getRaceProgress = () => {
    if (!raceStatus) return 0;
    return Math.round(raceStatus.progress * 100);
  };

  const getRemainingTime = () => {
    if (!raceStatus) return 120;
    return Math.max(0, Math.round(raceStatus.remaining_time));
  };

  const getChosenDriverPosition = () => {
    if (!finalPositions || !selectedDriver) {
      return null;
    }
    const chosenDriver = finalPositions.find(driver => driver.driver_name === selectedDriver.name);
    return chosenDriver;
  };

  const getRaceWinner = () => {
    if (!finalPositions) {
      return null;
    }
    const winner = finalPositions.find(driver => driver.position === 1);
    return winner;
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="digital-clock">
            {formatTime(currentTime)}
          </div>
          <div className="timer-display">
            {raceStatus ? `${getRemainingTime()}s` : '120s'}
          </div>
        </div>
        <h1>Live F1 Leaderboard</h1>
        <p>Real-time driver positions</p>
        {showMainApp && selectedDriver && (
          <div className="header-buttons">
            <button className="back-button" onClick={handleBackToSelection}>
              ← Change Driver
            </button>
            {raceStatus && raceStatus.status === 'in_progress' && (
              <button className="stop-race-button" onClick={handleStopRace}>
                🏁 Stop Race
              </button>
            )}
          </div>
        )}
      </header>
      
      {showRaceStarting && (
        <div className="race-starting-overlay">
          <div className="race-starting-animation">
            <div className="race-starting-content">
              <div className="race-starting-icon">🏁</div>
              <h2 className="race-starting-title">Race Starting!</h2>
              <p className="race-starting-subtitle">Get ready for {selectedDriver?.name}</p>
              <div className="race-starting-countdown">
                <div className="countdown-number">3</div>
                <div className="countdown-number">2</div>
                <div className="countdown-number">1</div>
                <div className="countdown-number go">GO!</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {showRaceFinished && (
        <div className="race-finished-overlay">
          <div className="race-finished-animation">
            <div className="race-finished-content">
              <div className="race-finished-icon">🏆</div>
              <h2 className="race-finished-title">Race Finished!</h2>
              
              <div className="race-results">
                <div className="race-winner">
                  <h3>Winner</h3>
                  <div className="winner-info">
                    <span className="winner-position">1st</span>
                    <span className="winner-name">{getRaceWinner()?.driver_name || 'Loading...'}</span>
                    <span className="winner-team">🏆 Winner</span>
                  </div>
                </div>
                
                <div className="chosen-driver-result">
                  <h3>Your Driver</h3>
                  <div className="driver-result-info">
                    <span className="driver-position">#{getChosenDriverPosition()?.position || '?'}</span>
                    <span className="driver-name">{selectedDriver?.name || 'Unknown Driver'}</span>
                    <span className="driver-team">{selectedDriver?.team || 'Unknown Team'}</span>
                  </div>
                </div>
              </div>
              
              <button 
                className="continue-button" 
                onClick={() => setShowRaceFinished(false)}
              >
                Continue to Leaderboard
              </button>
            </div>
          </div>
        </div>
      )}
      
      <main className={`app-main ${!showMainApp ? 'selection-mode' : ''}`}>
        {!showMainApp ? (
          <div className="selection-container">
            <DriverSelection 
              onDriverSelect={handleDriverSelect}
              selectedDriver={selectedDriver}
              isStartingRace={isStartingRace}
            />
          </div>
        ) : (
          <>
            {raceStatus && (
              <div className="race-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${getRaceProgress()}%` }}
                  ></div>
                </div>
                <div className="race-info">
                  {isRaceFinished ? (
                    <>
                      <span className="race-finished">🏁 Race Finished!</span>
                      <span className="race-finished">Final Progress: {getRaceProgress()}%</span>
                    </>
                  ) : (
                    <>
                      <span>Race Progress: {getRaceProgress()}%</span>
                      <span>Time Remaining: {getRemainingTime()}s</span>
                    </>
                  )}
                </div>
              </div>
            )}
            
            <div className="main-content-grid">
              <div className="leaderboard-section">
                <Leaderboard 
                  selectedDriver={selectedDriver} 
                  raceId={raceId}
                  raceStatus={raceStatus}
                />
              </div>
              
              {raceId && (
                <div className="avg-speed-section">
                  <AverageSpeedPanel 
                    raceId={raceId}
                    selectedDriver={selectedDriver}
                  />
                </div>
              )}
            </div>
            
          </>
        )}
      </main>
    </div>
  );
}

export default App;