import React, { useState, useEffect } from "react";
import { Routes, Route, Outlet, useNavigate, useLocation } from "react-router-dom";
import { MapPin, ShoppingCart } from "lucide-react";
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
import './App.css';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="search" element={<SearchResultsPage />} />
        <Route path="substitutions" element={<SubstitutionPage />} />
        <Route path="final-cart" element={<FinalCartPage />} />
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

  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogPage, setDialogPage] = useState('Trolley');
  const showNextButton = location.pathname === '/' || location.pathname === '/search';

  useEffect(() => {
    if (selectedStoreIds.size === 0) {
      setDialogPage('Edit Location');
      setDialogOpen(true);
    }
  }, []);

  const handleSearchSubmit = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && searchTerm.trim() !== '') {
      navigate(`/search?q=${encodeURIComponent(searchTerm.trim())}`);
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
    <div>
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-20 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-6">
            <a href="/" className="flex items-center space-x-2">
              <span className="font-bold text-2xl">SplitCart</span>
            </a>
          </div>
          <div className="flex flex-1 items-center justify-center">
            <div className="w-full max-w-sm">
              <Input
                type="search"
                placeholder="Search products, stores, and more..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={handleSearchSubmit}
                className="h-12 text-base"
              />
            </div>
          </div>
          <div className="flex items-center justify-end gap-2">
            <div className="flex items-center gap-1">
              <div className="relative">
                <Button variant="ghost" size="icon" className="h-14 w-14" onClick={() => openDialog('Trolley')}>
                  <ShoppingCart className="size-9" />
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
                  <MapPin className="size-9" />
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
            {showNextButton && <NextButton className="h-12 px-4" />}
          </div>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
      <SettingsDialog 
        open={dialogOpen} 
        onOpenChange={setDialogOpen} 
        defaultPage={dialogPage} 
      />
    </div>
  );
};

export default App;