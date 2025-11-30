import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext.tsx';
import { CartProvider } from './context/CartContext.tsx';
import { StoreListProvider } from './context/StoreListContext.tsx';
import { StoreSearchProvider } from './context/StoreSearchContext.tsx';
import { DialogProvider } from './context/DialogContext.tsx';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

const Root = () => {
  const { initialCart, initialStoreList } = useAuth();

  return (
    <CartProvider initialCart={initialCart}>
      <StoreListProvider initialStoreList={initialStoreList}>
        <StoreSearchProvider>
          <App />
        </StoreSearchProvider>
      </StoreListProvider>
    </CartProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter basename={import.meta.env.DEV ? '/static/' : '/'}>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <DialogProvider>
            <Root />
          </DialogProvider>
        </QueryClientProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
