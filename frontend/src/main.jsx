import { createRoot } from 'react-dom/client'
import './variables.css'
import './index.css'
import App from './App.jsx'

import { ShoppingListProvider } from './context/ShoppingListContext';
import { BrowserRouter } from 'react-router-dom';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')).render(
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ShoppingListProvider>
          <App />
        </ShoppingListProvider>
      </QueryClientProvider>
    </BrowserRouter>
)