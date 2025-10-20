import React, { useState, useEffect } from "react";
import { Routes, Route, Outlet, useNavigate, useLocation, Link } from "react-router-dom";
import { MapPin, ShoppingCart, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SettingsDialog } from "@/components/settings-dialog";
import { useStoreSelection } from "@/context/StoreContext";
import { useShoppingList } from "@/context/ShoppingListContext";
import { Badge } from "@/components/ui/badge";
import NextButton from "@/components/NextButton";
import HomePage from "./pages/HomePage";
import SearchResultsPage from "./pages/SearchResultsPage";
import SubstitutionPage from "./pages/SubstitutionPage";
import FinalCartPage from "./pages/FinalCartPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import { useAuth } from "@/context/AuthContext";
import CategoryBar from "./components/CategoryBar";
import Footer from './components/Footer';
import splitcartLogo from "./assets/splitcart_symbol_v6.png";
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
      </Route>
    </Routes>
  );
};

const Layout = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const { selectedStoreIds } = useStoreSelection();
  const { cartTotal } = useShoppingList();
  const { isAuthenticated, logout } = useAuth();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogPage, setDialogPage] = useState('Trolley');
  const showNextButton = (location.pathname === '/' || location.pathname === '/search') && cartTotal > 0;

  useEffect(() => {
    if (selectedStoreIds.size === 0) {
      setDialogPage('Edit Location');
      setDialogOpen(true);
    }
  }, []);

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
    if (page === 'Trolley' && selectedStoreIds.size === 0) {
      setDialogPage('Edit Location');
    } else {
      setDialogPage(page);
    }
    setDialogOpen(true);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-20 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-6">
            <a href="/" className="flex items-center space-x-2">
              <img src={splitcartLogo} alt="SplitCart Logo" className="h-16 w-16" />
              <span className="font-bold text-2xl">SplitCart</span>
            </a>
          </div>
          <div className="flex flex-1 items-center justify-center">
            <div className="relative w-full max-w-md">
              <Input
                type="search"
                placeholder="Search products, stores, and more..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                className="h-12 text-base pr-12 rounded-full"
              />
              <Button
                type="submit"
                size="icon"
                variant="secondary"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 rounded-full"
                onClick={handleSearch}
              >
                <Search className="h-5 w-5" />
                <span className="sr-only">Search</span>
              </Button>
            </div>
          </div>
          <div className="flex items-center justify-end gap-2">
            <div className="flex items-center gap-1">
              <div className="relative">
                <Button variant="ghost" size="icon" className="h-14 w-14" onClick={() => openDialog('Trolley')}>
                  <ShoppingCart className="size-10" />
                  <span className="sr-only">Open Trolley</span>
                </Button>
                {cartTotal > 0 && (
                  <Badge
                    variant="destructive"
                    className="absolute -right-1 -top-1 h-5 min-w-5 justify-center rounded-full px-1 font-mono tabular-nums"
                  >
                    {cartTotal}
                  </Badge>
                )}
              </div>
              <div className="relative">
                <Button variant="ghost" size="icon" className="h-14 w-14" onClick={() => openDialog('Edit Location')}>
                  <MapPin className="size-10" />
                  <span className="sr-only">Edit Location</span>
                </Button>
                {selectedStoreIds.size > 0 && (
                  <Badge
                    className="absolute -right-1 -top-1 h-5 min-w-5 justify-center rounded-full bg-blue-500 px-1 font-mono tabular-nums text-white"
                  >
                    {selectedStoreIds.size}
                  </Badge>
                )}
              </div>
            </div>
            {isAuthenticated ? (
              <Button variant="outline" onClick={logout}>Logout</Button>
            ) : (
              <Link to="/login">
                <Button variant="outline">Login</Button>
              </Link>
            )}
            {showNextButton && <NextButton className="h-12 px-4" />}
          </div>
        </div>
      </header>
      <CategoryBar />
      <main className="flex-grow">
        <Outlet />
      </main>
      <Footer />
      <SettingsDialog 
        open={dialogOpen} 
        onOpenChange={setDialogOpen} 
        defaultPage={dialogPage} 
      />
    </div>
  );
};

export default App;