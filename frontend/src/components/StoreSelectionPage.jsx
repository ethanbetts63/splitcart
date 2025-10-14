
import React from 'react';
import StoreMap from '../components/StoreMap';

const StoreSelectionPage = () => {
    return (
        <div style={{ padding: '2rem' }}>
            <h1 style={{ marginBottom: '1.5rem' }}>Select Your Stores</h1>
            <p style={{ marginBottom: '1.5rem' }}>Use the map below to select the stores you want to include in your price comparison.</p>
            <StoreMap />
        </div>
    );
};

export default StoreSelectionPage;
