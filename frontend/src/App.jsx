import React, { useState } from 'react';
import { Container } from 'react-bootstrap';
import Header from './components/Header';
import Footer from './components/Footer';
import SearchHeader from './components/SearchHeader';
import ProductGrid from './components/ProductGrid';
import './App.css';

function App() {
  const [searchTerm, setSearchTerm] = useState('');

  return (
    <div className="d-flex flex-column vh-100">
      <Header />
      <main className="flex-grow-1">
        <SearchHeader setSearchTerm={setSearchTerm} />
        <ProductGrid searchTerm={searchTerm} />
      </main>
      <Footer />
    </div>
  );
}

export default App;
