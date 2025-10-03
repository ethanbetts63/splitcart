
import React from 'react';
import StoreMap from '../components/StoreMap';
import { Container } from 'react-bootstrap';

const StoreSelectionPage = () => {
    return (
        <Container className="py-4">
            <h1 className="mb-4">Select Your Stores</h1>
            <p className="mb-4">Use the map below to select the stores you want to include in your price comparison.</p>
            <StoreMap />
        </Container>
    );
};

export default StoreSelectionPage;
