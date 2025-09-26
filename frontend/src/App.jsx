import React from 'react';
import { Container } from 'react-bootstrap';
import Header from './components/Header';
import Footer from './components/Footer';
import './App.css';

function App() {
  return (
    <div className="d-flex flex-column vh-100">
      <Header />
      <main className="flex-grow-1">
        <Container className="mt-4">
          <h1>Welcome to SplitCart</h1>
          <p>This is where the product list will go.</p>
        </Container>
      </main>
      <Footer />
    </div>
  );
}

export default App;