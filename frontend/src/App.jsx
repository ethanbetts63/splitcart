import React from 'react';
import { Header } from './components/Header';
import { ProductCarousel } from './components/ProductCarousel';

function App() {
  return (
    <div>
      <Header />
      <main className="container mx-auto p-4">
        <h1 className="text-2xl font-bold">Welcome to SplitCart</h1>
        <p>Your grocery comparison tool.</p>

        <section className="mt-8">
          <h2 className="text-xl font-semibold">Featured Products</h2>
          <div className="mt-4 flex justify-center">
            <ProductCarousel />
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;