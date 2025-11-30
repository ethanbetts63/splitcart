import React, { useState, Suspense } from "react";
import { Routes, Route, Outlet, useNavigate, useLocation } from "react-router-dom";
import { SettingsDialog } from "./components/settings-dialog";
import { useStoreList } from "./context/StoreListContext";
import { useCart } from "./context/CartContext";
import NextButton from "./components/NextButton";
import LoadingSpinner from "./components/LoadingSpinner";
import { Toaster } from "./components/ui/sonner";
import { useDialog } from "./context/DialogContext";

import HomePage from "./pages/HomePage";

// Lazy load page components
const SearchResultsPage = React.lazy(() => import("./pages/SearchResultsPage"));
const SubstitutionPage = React.lazy(() => import("./pages/SubstitutionPage"));
const FinalCartPage = React.lazy(() => import("./pages/FinalCartPage"));
const LoginPage = React.lazy(() => import("./pages/LoginPage"));
const SignupPage = React.lazy(() => import("./pages/SignupPage"));
const ContactPage = React.lazy(() => import("./pages/ContactPage"));
const PillarPage = React.lazy(() => import("./pages/PillarPage"));
const ProductPage = React.lazy(() => import("./pages/ProductPage"));
const BargainsPage = React.lazy(() => import("./pages/BargainsPage"));

import { useAuth } from "./context/AuthContext";
import CategoryBar from "./components/CategoryBar";
import Footer from './components/Footer';
import NavBar from './components/NavBar';
import './App.css';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="search" element={<SearchResultsPage />} />
        <Route path="substitutions" element={<SubstitutionPage />} />
        <Route path="final-cart" element={<FinalCartPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/categories/:slug" element={<PillarPage />} />
        <Route path="/product/:slug" element={<ProductPage />} />
        <Route path="/bargains" element={<BargainsPage />} />
      </Route>
    </Routes>
  );
};

const Layout = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const { selectedStoreIds } = useStoreList();
  const { currentCart } = useCart();
  const items = currentCart ? currentCart.items : [];
  const cartTotal = items.length;
  const { isAuthenticated, logout } = useAuth();
  
  // Get dialog state and functions from the new context
  const { isDialogOpen, dialogPage, openDialog, closeDialog } = useDialog();

  const showNextButton = (location.pathname === '/' || location.pathname === '/search') && cartTotal > 0 && !isDialogOpen;

  // The problematic useEffect that caused the global click issue has been removed.

  const handleSearch = () => {
    if (searchTerm.trim() !== '') {
      navigate(`/search?q=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  const handleSearchKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };
  
  // This function now just calls the context function.
  // It also handles the special case of checking for selected stores when opening the cart.
  const handleOpenDialog = (page: string) => {
    if (page === 'cart' && selectedStoreIds.size === 0) {
      openDialog('Edit Location');
    } else {
      openDialog(page);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <NavBar
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        handleSearch={handleSearch}
        handleSearchKeyDown={handleSearchKeyDown}
        openDialog={handleOpenDialog} // Pass the new handler
        cartTotal={cartTotal}
        selectedStoreIds={selectedStoreIds}
        isAuthenticated={isAuthenticated}
        logout={logout}
      />
      {(location.pathname === '/' || location.pathname === '/search' || location.pathname.startsWith('/categories/') || location.pathname.startsWith('/product/')) && <CategoryBar />}
      <main className="flex-grow">
        <Suspense fallback={<LoadingSpinner fullScreen />}>
          <Outlet />
        </Suspense>
      </main>
      <Footer />
      <SettingsDialog 
        open={isDialogOpen} 
        onOpenChange={(isOpen) => { if (!isOpen) closeDialog() }}
        defaultPage={dialogPage} 
      />
      <Toaster />
      {showNextButton && (
        <NextButton className="fixed bottom-8 right-8 z-50 h-16 w-16 rounded-full shadow-lg" />
      )}
    </div>
  );
};

export default App;