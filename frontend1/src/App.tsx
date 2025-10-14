import React, { useState } from "react";
import { Routes, Route, Outlet, useNavigate } from "react-router-dom";
import { MapPin, ShoppingCart } from "lucide-react"; // Import icons
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SettingsDialog } from "@/components/settings-dialog";
import HomePage from "./pages/HomePage";
import SearchResultsPage from "./pages/SearchResultsPage";
import './App.css';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="search" element={<SearchResultsPage />} />
        {/* Add other routes here as needed */}
      </Route>
    </Routes>
  );
};

const Layout = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();

  // State for controlling the settings dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogPage, setDialogPage] = useState('Trolley');

  const handleSearchSubmit = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && searchTerm.trim() !== '') {
      navigate(`/search?q=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  const openDialog = (page: string) => {
    setDialogPage(page);
    setDialogOpen(true);
  };

  return (
    <div>
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          {/* Left side */}
          <div className="flex items-center gap-6">
            <a href="/" className="flex items-center space-x-2">
              <span className="font-bold text-lg">SplitCart</span>
            </a>
          </div>

          {/* Center Search Bar */}
          <div className="flex flex-1 items-center justify-center">
            <div className="w-full max-w-sm">
              <Input
                type="search"
                placeholder="Search products, stores, and more..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={handleSearchSubmit}
              />
            </div>
          </div>

          {/* Right side Icon Buttons */}
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="icon" onClick={() => openDialog('Trolley')}>
              <ShoppingCart className="h-6 w-6" />
              <span className="sr-only">Open Trolley</span>
            </Button>
            <Button variant="ghost" size="icon" onClick={() => openDialog('Edit Location')}>
              <MapPin className="h-6 w-6" />
              <span className="sr-only">Edit Location</span>
            </Button>
          </div>
        </div>
      </header>

      {/* The main page content will be rendered here */}
      <main>
        <Outlet />
      </main>

      {/* The Settings Dialog is now controlled by the Layout state */}
      <SettingsDialog 
        open={dialogOpen} 
        onOpenChange={setDialogOpen} 
        defaultPage={dialogPage} 
      />
    </div>
  );
};

export default App;