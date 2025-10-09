import { createRoot } from 'react-dom/client'
import './css/variables.css'
import './css/index.css'
import App from './App.jsx'

import { ProductCacheProvider } from './context/ProductCacheContext';
import { ShoppingListProvider } from './context/ShoppingListContext';
import { BrowserRouter } from 'react-router-dom';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')).render(
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ProductCacheProvider>
          <ShoppingListProvider>
            <App />
          </ShoppingListProvider>
        </ProductCacheProvider>
      </QueryClientProvider>
    </BrowserRouter>
)