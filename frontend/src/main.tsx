import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ShoppingListProvider } from './context/ShoppingListContext';
import { SubstitutionProvider } from './context/SubstitutionContext';
import { StoreSearchProvider } from './context/StoreSearchContext';
import { StoreListProvider } from './context/StoreListContext';
import { AuthProvider } from './context/AuthContext';
import { Toaster } from 'sonner';
import './index.css'
import App from './App.tsx'

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
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
    <ReactQueryDevtools initialIsOpen={false} />
  </QueryClientProvider>
)


