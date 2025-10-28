import React from 'react';
import { Link } from 'react-router-dom';
import { MapPin, ShoppingCart, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import NextButton from '@/components/NextButton';
import splitcartLogo from "../assets/splitcart_symbol_v6.png";

interface NavBarProps {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  handleSearch: () => void;
  handleSearchKeyDown: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  openDialog: (page: string) => void;
  cartTotal: number;
  selectedStoreIds: Set<number>;
  isAuthenticated: boolean;
  logout: () => void;
  showNextButton: boolean;
}

const NavBar: React.FC<NavBarProps> = ({
  searchTerm,
  setSearchTerm,
  handleSearch,
  handleSearchKeyDown,
  openDialog,
  cartTotal,
  selectedStoreIds,
  isAuthenticated,
  logout,
  showNextButton,
}) => {
  return (
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
              <Button variant="ghost" size="icon" className="h-14 w-14" onClick={() => openDialog('cart')}>
                <ShoppingCart className="size-10" />
                <span className="sr-only">Open cart</span>
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
  );
};

export default NavBar;
