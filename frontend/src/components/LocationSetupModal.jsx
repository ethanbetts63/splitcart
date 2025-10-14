import React, { useState, useEffect } from 'react';

const LocationSetupModal = ({ show, onHide, onSave }) => {
  const [postcode, setPostcode] = useState('');
  const [radius, setRadius] = useState(10); // Default radius in km

  const handleSave = () => {
    if (postcode && radius > 0) {
      onSave({ postcode, radius });
      onHide();
    }
  };

  if (!show) {
    return null;
  }

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1050 }}>
      <div style={{ background: 'var(--bg-light)', padding: '2rem', borderRadius: '8px', minWidth: '300px' }}>
        <div>
          <h3>Set Your Location Preferences</h3>
        </div>
        <div>
          <p>To provide you with the most relevant product information, please tell us your preferred location and travel range.</p>
          <form>
            <div style={{ marginBottom: '1rem' }}>
              <label>Postcode</label>
              <input
                type="text"
                placeholder="e.g., 3000"
                value={postcode}
                onChange={(e) => setPostcode(e.target.value)}
                style={{ width: '100%', padding: '0.5rem' }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label>Travel Radius (km)</label>
              <div style={{ display: 'flex' }}>
                <button type="button" onClick={() => setRadius(Math.max(1, radius - 1))}>-</button>
                <input
                  type="number"
                  value={radius}
                  onChange={(e) => setRadius(parseInt(e.target.value) || 1)}
                  min="1"
                  style={{ textAlign: 'center', width: '50px' }}
                />
                <button type="button" onClick={() => setRadius(radius + 1)}>+</button>
              </div>
            </div>
          </form>
        </div>
        <div>
          <button onClick={handleSave}>Save Location</button>
          <button onClick={onHide} style={{ marginLeft: '1rem' }}>Close</button>
        </div>
      </div>
    </div>
  );
};

export default LocationSetupModal;
