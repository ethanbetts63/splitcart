import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import GridSourcer from './components/GridSourcer'; // Import GridSourcer
import ScrollerManager from './components/ScrollerManager';
import LocationSetupModal from './components/LocationSetupModal';
import Layout from './components/Layout'; // Import Layout component
import SubstitutionPage from './pages/SubstitutionPage';
import ProductListPage from './pages/ProductListPage'; // Import ProductListPage
import FinalCartPage from './pages/FinalCartPage';
import Background from './components/Background';
import { useShoppingList } from './context/ShoppingListContext';

import StoreMap from './components/StoreMap';
import './App.css';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [showStoreMap, setShowStoreMap] = useState(false);
  const { setUserLocation, nearbyStoreIds, isLocationLoaded, setSelectedStoreIds } = useShoppingList();

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
        { title: "Popular with SplitCart users", searchTerm: "", seeMoreLink: "/products?source=all" },
        ...randomSearchTerms.map(term => ({ title: term, searchTerm: term, seeMoreLink: `/products?search=${encodeURIComponent(term)}` }))
    ];
    setScrollers(scrollerConfig);
  }, []);

  const handleSaveLocation = (location) => {
    setUserLocation(location);
    localStorage.setItem('userLocation', JSON.stringify(location));
    setShowLocationModal(false);
  };

  return (
        <div style={{ minHeight: '100vh' }}>
      <Background />
      <Header 
        onShowLocationModal={() => setShowLocationModal(true)} 
        onShowStoreMap={() => setShowStoreMap(true)} 
        setSearchTerm={setSearchTerm} 
      />
            <main>
        <Routes>
          <Route path="/" element={
            <Layout searchTerm={searchTerm} setSearchTerm={setSearchTerm}>
              {searchTerm ? (
                <GridSourcer searchTerm={searchTerm} nearbyStoreIds={nearbyStoreIds} />
              ) : (
                <ScrollerManager scrollers={scrollers} nearbyStoreIds={nearbyStoreIds} isLocationLoaded={isLocationLoaded} />
              )}
            </Layout>
          } />
          <Route path="/products" element={
            <Layout searchTerm={searchTerm} setSearchTerm={setSearchTerm}>
              <ProductListPage nearbyStoreIds={nearbyStoreIds} />
            </Layout>
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

            <div className={`off-canvas-menu ${showStoreMap ? 'visible' : ''}`} style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem' }}>
                <h1 style={{ fontFamily: 'Vollkorn', fontStyle: 'italic', fontSize: '60px', color: 'var(--primary)', textAlign: 'center', flex: 1, marginBottom: '0' }}>
                  select stores
                </h1>
                <button onClick={() => setShowStoreMap(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem' }}>&times;</button>
              </div>
              <div style={{ padding: '1rem', flex: 1, overflowY: 'auto' }}>
                <StoreMap onSelectionChange={setSelectedStoreIds} />
              </div>
            </div>    </div>
  );
}

export default App;
