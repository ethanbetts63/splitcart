import React, { useState, useEffect } from 'react';
import { Container } from 'react-bootstrap';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import SearchHeader from './components/SearchHeader';
import ProductGrid from './components/ProductGrid';
import HorizontalProductScroller from './components/HorizontalProductScroller';
import LocationSetupModal from './components/LocationSetupModal';
import SubstitutionPage from './pages/SubstitutionPage'; // Import the new page
import './App.css';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [userLocation, setUserLocation] = useState(null); // { postcode: 'XXXX', radius: Y }

  useEffect(() => {
    const savedLocation = localStorage.getItem('userLocation');
    if (savedLocation) {
      setUserLocation(JSON.parse(savedLocation));
    } else {
      setShowLocationModal(true);
    }
  }, []);

  const handleSaveLocation = (location) => {
    setUserLocation(location);
    localStorage.setItem('userLocation', JSON.stringify(location));
    setShowLocationModal(false);
  };

  return (
    <div className="d-flex flex-column vh-100">
      <Header onShowLocationModal={() => setShowLocationModal(true)} />
      <main className="flex-grow-1">
        <Routes>
          <Route path="/" element={
            <>
              <SearchHeader setSearchTerm={setSearchTerm} />
              <Container fluid>
                <HorizontalProductScroller title="Bargain Finds!" />
                <ProductGrid searchTerm={searchTerm} userLocation={userLocation} />
              </Container>
            </>
          } />
          <Route path="/split-cart" element={<SubstitutionPage />} />
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