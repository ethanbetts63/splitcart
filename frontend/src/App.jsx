import React, { useState, useEffect } from 'react';
import { Container } from 'react-bootstrap';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import SearchHeader from './components/SearchHeader';
import ProductGrid from './components/ProductGrid';
import ScrollerManager from './components/ScrollerManager';
import LocationSetupModal from './components/LocationSetupModal';
import SubstitutionPage from './pages/SubstitutionPage';
import FinalCartPage from './pages/FinalCartPage';
import './App.css';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [nearbyStoreIds, setNearbyStoreIds] = useState([]);

  const scrollerTitles = [
    "Bargain Finds!",
    "Popular with SplitCart users",
    "Milk",
    "Bread",
    "Eggs"
  ];

  useEffect(() => {
    const savedLocation = localStorage.getItem('userLocation');
    if (savedLocation) {
      setUserLocation(JSON.parse(savedLocation));
    } else {
      setShowLocationModal(true);
    }
  }, []);

  useEffect(() => {
    const fetchStoreIds = async () => {
      if (userLocation && userLocation.postcode && userLocation.radius) {
        try {
          const response = await fetch(`/api/stores/nearby/?postcode=${userLocation.postcode}&radius=${userLocation.radius}`);
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          const data = await response.json();
          setNearbyStoreIds(data);
        } catch (error) {
          console.error("Error fetching nearby store IDs:", error);
          setNearbyStoreIds([]);
        }
      }
    };
    fetchStoreIds();
  }, [userLocation]);

  const handleSaveLocation = (location) => {
    setUserLocation(location);
    localStorage.setItem('userLocation', JSON.stringify(location));
    setShowLocationModal(false);
  };

  return (
    <div className="d-flex flex-column" style={{ minHeight: '100vh' }}>
      <Header onShowLocationModal={() => setShowLocationModal(true)} setSearchTerm={setSearchTerm} />
      <main className="flex-grow-1">
        <Routes>
          <Route path="/" element={
            <>
              <SearchHeader searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
              <Container fluid>
                {searchTerm ? (
                  <ProductGrid searchTerm={searchTerm} nearbyStoreIds={nearbyStoreIds} />
                ) : (
                  <ScrollerManager titles={scrollerTitles} />
                )}
              </Container>
            </>
          } />
          <Route path="/split-cart" element={<SubstitutionPage nearbyStoreIds={nearbyStoreIds} />} />
          <Route path="/final-cart" element={<FinalCartPage />} />
        </Routes>
      </main>

      <Footer />

      <LocationSetupModal
        show={showLocationModal}
        onHide={() => setShowLocationModal(false)}
        onSave={handleSaveLocation}
      />
    </div>
  );
}

export default App;
