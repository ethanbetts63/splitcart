import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ShoppingListProvider } from './context/ShoppingListContext';
import { SubstitutionProvider } from './context/SubstitutionContext';
import { StoreProvider } from './context/StoreContext'
import { AuthProvider } from './context/AuthContext';
import { Toaster } from 'sonner';
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
    <BrowserRouter>
      <AuthProvider>
        <StoreProvider>
          <ShoppingListProvider>
            <SubstitutionProvider>
              <App />
              <Toaster />
            </SubstitutionProvider>
          </ShoppingListProvider>
        </StoreProvider>
      </AuthProvider>
    </BrowserRouter>
)


