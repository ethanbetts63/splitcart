import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ShoppingListProvider } from './context/ShoppingListContext'
import { StoreProvider } from './context/StoreContext'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <StoreProvider>
        <ShoppingListProvider>
          <App />
        </ShoppingListProvider>
      </StoreProvider>
    </BrowserRouter>
  </StrictMode>,
)
