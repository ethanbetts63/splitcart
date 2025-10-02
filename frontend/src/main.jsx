import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'bootstrap/dist/css/bootstrap.min.css'
import './index.css'
import App from './App.jsx'

import { ShoppingListProvider } from './context/ShoppingListContext';
import { BrowserRouter } from 'react-router-dom';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'; // Import QueryClient and QueryClientProvider

const queryClient = new QueryClient(); // Create a client

createRoot(document.getElementById('root')).render(
  // <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}> {/* Wrap with QueryClientProvider */}
        <ShoppingListProvider>
          <App />
        </ShoppingListProvider>
      </QueryClientProvider>
    </BrowserRouter>
  // </StrictMode>,
)