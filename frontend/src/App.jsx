import React from 'react';
import { Header } from './components/Header';

function App() {
  return (
    <div>
      <Header />
      <main className="container mx-auto p-4">
        <h1 className="text-2xl font-bold">Welcome to SplitCart</h1>
        <p>Your grocery comparison tool.</p>
      </main>
    </div>
  );
}

export default App;