import React, { useState, useEffect, Suspense } from "react";
import { Routes, Route, Outlet, useNavigate, useLocation } from "react-router-dom";
import { SettingsDialog } from "./components/settings-dialog";
import { useStoreList } from "./context/StoreListContext";
import { useCart } from "./context/CartContext";
import NextButton from "./components/NextButton";
import LoadingSpinner from "./components/LoadingSpinner";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";

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

  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogPage, setDialogPage] = useState('cart');
  const showNextButton = (location.pathname === '/' || location.pathname === '/search') && cartTotal > 0 && !dialogOpen;

  useEffect(() => {
    const handleInteraction = (event: MouseEvent | KeyboardEvent) => {
      if (
        !dialogOpen &&
        location.pathname === '/' &&
        selectedStoreIds.size === 0
      ) {
        if (event instanceof KeyboardEvent && event.key !== 'Enter') {
          return;
        }

        const target = event.target as HTMLElement;
        // Allow navigation links in header and footer and FAQ items to work normally.
        if (target.closest('header a[href], footer a[href], .faq-item')) {
            return;
        }

        // For other interactions, open the dialog and stop the event.
        event.preventDefault();
        event.stopPropagation();
        openDialog('Edit Location');
        toast.info("Please select stores to continue.");
      }
    };

    // Use capture phase to intercept events early.
    document.addEventListener('click', handleInteraction, true);
    document.addEventListener('keydown', handleInteraction, true);

    return () => {
      document.removeEventListener('click', handleInteraction, true);
      document.removeEventListener('keydown', handleInteraction, true);
    };
  }, [dialogOpen, location.pathname, selectedStoreIds.size]);

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

  const openDialog = (page: string) => {
    if (page === 'cart' && selectedStoreIds.size === 0) {
      setDialogPage('Edit Location');
    } else {
      setDialogPage(page);
    }
    setDialogOpen(true);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <NavBar
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        handleSearch={handleSearch}
        handleSearchKeyDown={handleSearchKeyDown}
        openDialog={openDialog}
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
        open={dialogOpen} 
        onOpenChange={setDialogOpen} 
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