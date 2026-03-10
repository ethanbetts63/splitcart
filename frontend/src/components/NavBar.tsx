import React from 'react';
import { Link } from 'react-router-dom';
import { MapPin, ShoppingCart, Search } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import splitcartLogo from "../assets/splitcart_symbol_v6.webp";
import splitcartLogo320 from "../assets/splitcart_symbol_v6-320w.webp";
import splitcartLogo640 from "../assets/splitcart_symbol_v6-640w.webp";
import splitcartLogo768 from "../assets/splitcart_symbol_v6-768w.webp";
import splitcartLogo1024 from "../assets/splitcart_symbol_v6-1024w.webp";
import splitcartLogo1280 from "../assets/splitcart_symbol_v6-1280w.webp";
import type { NavBarProps } from '../types/NavBarProps';

const SearchBar = ({
  searchTerm,
  setSearchTerm,
  handleSearchKeyDown,
  handleSearch,
  className = '',
}: {
  searchTerm: string;
  setSearchTerm: (v: string) => void;
  handleSearchKeyDown: React.KeyboardEventHandler<HTMLInputElement>;
  handleSearch: () => void;
  className?: string;
}) => (
  <div className={`relative w-full ${className}`}>
    <Input
      type="search"
      placeholder="Search products, stores, and more..."
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
      onKeyDown={handleSearchKeyDown}
      className="h-10 text-base pr-12 rounded-full"
    />
    <Button
      type="submit"
      size="icon"
      variant="secondary"
      className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 rounded-full"
      onClick={handleSearch}
    >
      <Search className="h-4 w-4" />
      <span className="sr-only">Search</span>
    </Button>
  </div>
);

const NavBar: React.FC<NavBarProps> = ({
  searchTerm,
  setSearchTerm,
  handleSearch,
  handleSearchKeyDown,
  openDialog,
  cartTotal,
  selectedStoreIds,
  isUserDefinedList,
  isAuthenticated,
  logout,
}) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white">

      {/* ── Main row ── */}
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8 gap-4">

        {/* Logo */}
        <a href="/" className="flex items-center space-x-2 flex-shrink-0">
          <img
            src={splitcartLogo}
            srcSet={`${splitcartLogo320} 320w, ${splitcartLogo640} 640w, ${splitcartLogo768} 768w, ${splitcartLogo1024} 1024w, ${splitcartLogo1280} 1280w`}
            sizes="48px"
            alt="SplitCart Logo"
            className="h-12 w-12 sm:h-14 sm:w-14 flex-shrink-0"
          />
          <span className="font-bold text-2xl hidden md:block bg-yellow-300 px-0.5 py-1 rounded italic text-black">
            SplitCart
          </span>
        </a>

        {/* Search — desktop only (hidden on mobile) */}
        <div className="hidden sm:flex flex-1 items-center justify-center">
          <SearchBar
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            handleSearchKeyDown={handleSearchKeyDown}
            handleSearch={handleSearch}
            className="max-w-md"
          />
        </div>

        {/* Icons + auth */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <div className="relative">
            <Button variant="ghost" size="icon" className="h-10 w-10 sm:h-12 sm:w-12" onClick={() => openDialog('cart')}>
              <ShoppingCart className="size-6 sm:size-7" />
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
            <Button variant="ghost" size="icon" className="h-10 w-10 sm:h-12 sm:w-12" onClick={() => openDialog('Edit Location')}>
              <MapPin className="size-6 sm:size-7" />
              <span className="sr-only">Edit Location</span>
            </Button>
            {isUserDefinedList && selectedStoreIds.size > 0 && (
              <Badge className="absolute -right-1 -top-1 h-5 min-w-5 justify-center rounded-full bg-blue-500 px-1 font-mono tabular-nums text-white">
                {selectedStoreIds.size}
              </Badge>
            )}
          </div>
          {isAuthenticated ? (
            <Button variant="outline" size="sm" onClick={logout}>Logout</Button>
          ) : (
            <Link to="/login">
              <Button variant="outline" size="sm">Login</Button>
            </Link>
          )}
        </div>
      </div>

      {/* ── Search row — mobile only ── */}
      <div className="sm:hidden px-4 pb-3">
        <SearchBar
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          handleSearchKeyDown={handleSearchKeyDown}
          handleSearch={handleSearch}
        />
      </div>

    </header>
  );
};

export default NavBar;
