import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ShoppingListProvider } from './context/ShoppingListContext';
import { SubstitutionProvider } from './context/SubstitutionContext';
import { StoreSearchProvider } from './context/StoreSearchContext';
import { StoreListProvider } from './context/StoreListContext';
import { AuthProvider } from './context/AuthContext';
import { Toaster } from 'sonner';
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
    <BrowserRouter>
      <AuthProvider>
        <StoreSearchProvider>
          <StoreListProvider>
            <ShoppingListProvider>
              <SubstitutionProvider>
                <App />
                <Toaster position="top-center" />
              </SubstitutionProvider>
            </ShoppingListProvider>
          </StoreListProvider>
        </StoreSearchProvider>
      </AuthProvider>
    </BrowserRouter>
)


