import { useState, useEffect } from 'react';

export const useDriverPositions = (positionsData) => {
  const [driverPositions, setDriverPositions] = useState([]);
  const [highlightedDrivers, setHighlightedDrivers] = useState(new Set());

  useEffect(() => {
    if (positionsData?.data?.positions) {
      const newPositions = positionsData.data.positions;
      
      // Find drivers whose positions changed
      const changedDrivers = new Set();
      
      if (driverPositions.length > 0) {
        newPositions.forEach(newPos => {
          const oldPos = driverPositions.find(old => old.driver_name === newPos.driver_name);
          if (oldPos && oldPos.position !== newPos.position) {
            changedDrivers.add(newPos.driver_name);
          }
        });
      }
      
      // Update positions
      setDriverPositions(newPositions);
      
      // Highlight changed drivers
      if (changedDrivers.size > 0) {
        setHighlightedDrivers(changedDrivers);
        
        // Remove highlight after 2 seconds
        setTimeout(() => {
          setHighlightedDrivers(new Set());
        }, 2000);
      }
    }
  }, [positionsData]);

  return { driverPositions, highlightedDrivers };
};
