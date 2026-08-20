import React from 'react';

const DriverRow = ({ driver, position, speed, isHighlighted, isSelectedDriver, teamColor, previousPosition }) => {
  return (
    <tr 
      className={`driver-row ${isHighlighted ? 'highlighted' : ''} ${isSelectedDriver ? 'selected-driver' : ''}`}
    >
      <td className="position-cell">
        {position}
      </td>
      <td className="driver-cell">
        <div className="driver-info">
          <img 
            src={`https://placehold.co/40x40/${teamColor?.replace('#', '')}/FFFFFF?text=${driver?.name?.charAt(0) || 'D'}`}
            alt={driver?.name || 'Driver'}
            className="driver-logo"
            style={{ borderColor: teamColor }}
          />
          <div className="driver-details">
            <div className="driver-name">{driver?.name || 'Unknown Driver'}</div>
            <div className="team-name">{driver?.team || 'Unknown Team'}</div>
          </div>
        </div>
      </td>
      <td className="hidden sm:table-cell team-cell">
        {driver?.team || 'Unknown Team'}
      </td>
      <td className="speed-cell">
        {speed ? `${speed.toFixed(1)} km/h` : '--'}
      </td>
    </tr>
  );
};

export default DriverRow;
