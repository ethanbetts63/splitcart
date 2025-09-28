import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'bootstrap/dist/css/bootstrap.min.css'
import './index.css'
import App from './App.jsx'

import { ShoppingListProvider } from './context/ShoppingListContext';
import { BrowserRouter } from 'react-router-dom';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <ShoppingListProvider>
        <App />
      </ShoppingListProvider>
    </BrowserRouter>
  </StrictMode>,
)
