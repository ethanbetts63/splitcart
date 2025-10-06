import React from 'react';
import mapIcon from '../assets/edit_location_large.svg';
import './MapButton.css';

const MapButton = ({ onClick }) => {
  return (
    <button onClick={onClick} className="map-button">
      <img src={mapIcon} alt="Map" />
    </button>
  );
};

export default MapButton;
