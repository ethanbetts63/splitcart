import React, { useState, useEffect } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import OffCanvasMenu from './components/OffCanvasMenu';
import Footer from './components/Footer';
import GridSourcer from './components/GridSourcer';
import ScrollerManager from './components/ScrollerManager';
import LocationSetupModal from './components/LocationSetupModal';
import SubstitutionPage from './pages/SubstitutionPage';
import ProductListPage from './pages/ProductListPage';
import FinalCartPage from './pages/FinalCartPage';

import InstructionsTile from './components/InstructionsTile';
import BottomInfoCard from './components/BottomInfoCard';
import SplitCartButton from './components/SplitCartButton';
import Backdrop from './components/Backdrop';
import { useShoppingList } from './context/ShoppingListContext';
import './css/App.css';
import backgroundImage from './assets/background_main_page.png';
import bottomImage from './assets/bottom_image.png';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [isOffCanvasOpen, setIsOffCanvasOpen] = useState(false);
  const [offCanvasContent, setOffCanvasContent] = useState(null);

  const { items, setUserLocation, nearbyStoreIds, isLocationLoaded, setSelectedStoreIds } = useShoppingList();
  const location = useLocation();
  const navigate = useNavigate();

  const [scrollers, setScrollers] = useState([]);

  useEffect(() => {
    const commonSearches = [
      "Full Cream Milk", "Free Range Eggs", "Sourdough Bread", "Butter", "Cheese",
      "Chicken Breast", "Beef Mince", "Sausages", "Apples", "Bananas", "Broccoli",
      "Carrots", "Onions", "Potatoes", "Tomatoes", "Pasta", "Rice", "Cereal",
      "Coffee", "Tea", "Yoghurt", "Ice Cream", "Chocolate", "Biscuits", "Chips",
      "Soft Drink", "Juice", "Beer", "Wine", "Toilet Paper"
    ];
    const getRandomItems = (arr, n) => {
      const shuffled = [...arr].sort(() => 0.5 - Math.random());
      return shuffled.slice(0, n);
    };
    const randomSearchTerms = getRandomItems(commonSearches, 3);
    const scrollerConfig = [
        { title: "Bargain Finds!", sourceUrl: "/api/products/bargains/", seeMoreLink: "/products?source=bargains" },

        ...randomSearchTerms.map(term => ({ title: term, searchTerm: term, seeMoreLink: `/products?search=${encodeURIComponent(term)}` }))
    ];
    setScrollers(scrollerConfig);
  }, []);

  const handleSaveLocation = (location) => {
    setUserLocation(location);
    localStorage.setItem('userLocation', JSON.stringify(location));
    setShowLocationModal(false);
  };

  const handleShowTrolley = () => {
    setOffCanvasContent('trolley');
    setIsOffCanvasOpen(true);
  };

  const handleShowMap = () => {
    setOffCanvasContent('map');
    setIsOffCanvasOpen(true);
  };

  const handleCloseOffCanvas = () => {
    setIsOffCanvasOpen(false);
  };

  const handleNavigateHome = () => {
    handleCloseOffCanvas();
    setSearchTerm('');
    navigate('/');
  };

  const handleLocationChange = () => {
    handleCloseOffCanvas();
    setShowLocationModal(true);
  };

  return (
    <div style={{ minHeight: '100vh' }}>

      <Navbar 
        searchTerm={searchTerm} 
        setSearchTerm={setSearchTerm} 
        onShowTrolley={handleShowTrolley} 
        onShowMap={handleShowMap} 
      />
      <div className="content-container">
        {!searchTerm && location.pathname === '/' && (
          <>
            <img src={backgroundImage} className="scrolling-background-image" alt="background" />
            <img src={bottomImage} className="bottom-left-image" alt="bottom background" />
          </>
        )}
        <main>
          {!searchTerm && (
            <>
              <div className="hero-section">
                <h2 className="subtitle">Supermarkets have algorithms. Now so do you.</h2>
                <p className="subtext">The math behind your grocery run — done by AI, not guesswork.</p>
              </div>
              <InstructionsTile />
            </>
          )}
          <Routes>
          <Route path="/" element={
            searchTerm ? (
              <GridSourcer searchTerm={searchTerm} nearbyStoreIds={nearbyStoreIds} />
            ) : (
              <ScrollerManager scrollers={scrollers} nearbyStoreIds={nearbyStoreIds} isLocationLoaded={isLocationLoaded} />
            )
          } />
          <Route path="/products" element={<ProductListPage nearbyStoreIds={nearbyStoreIds} />} />
          <Route path="/split-cart" element={<SubstitutionPage nearbyStoreIds={nearbyStoreIds} />} />
          <Route path="/final-cart" element={<FinalCartPage />} />
        </Routes>
        </main>
        {!searchTerm && location.pathname === '/' && <BottomInfoCard />}
      </div>

      <Footer />

      <LocationSetupModal
        show={showLocationModal}
        onHide={() => setShowLocationModal(false)}
        onSave={handleSaveLocation}
      />

      <Backdrop show={isOffCanvasOpen} onClick={handleCloseOffCanvas} />

      <OffCanvasMenu 
        isOpen={isOffCanvasOpen}
        onClose={handleCloseOffCanvas}
        content={offCanvasContent}
        onLocationChange={handleLocationChange}
        onStoreSelectionChange={setSelectedStoreIds}
        onNavigateHome={handleNavigateHome}
      />

      {items.length > 0 && location.pathname !== '/split-cart' && location.pathname !== '/final-cart' && (
        <div style={{ position: 'fixed', bottom: '2rem', right: '2rem', zIndex: 1040 }}>
          <SplitCartButton />
        </div>
      )}
    </div>
  );
}

export default App;
