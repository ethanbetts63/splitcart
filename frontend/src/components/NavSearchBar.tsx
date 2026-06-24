"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

export function NavSearchBar({ className = "" }: { className?: string }) {
  const [searchTerm, setSearchTerm] = useState("");
  const router = useRouter();

  const handleSearch = () => {
    if (searchTerm.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  return (
    <div className={`relative w-full ${className}`}>
      <Input
        type="search"
        placeholder="Search products, stores, and more..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
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
}
