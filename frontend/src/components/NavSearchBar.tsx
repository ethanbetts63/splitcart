'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';
import { Button } from './common/button';
import { Input } from './common/input';
import { cn } from '@/lib/utils';

/**
 * How wide the bar is allowed to get. Two values, because the header draws it
 * twice and the difference is structural rather than decorative: on the main
 * row it shares the line with the logo and the cart and auth buttons, so it is
 * capped or it swallows them; on the phone row below it is the only thing
 * there and runs the full width.
 *
 * This replaced an open `className` passthrough, which is the shape
 * `component-registry.md` REG-6 rules out — a caller could reposition or
 * restyle the bar from outside and nothing named what it was allowed to
 * change.
 */
export type NavSearchBarWidth = 'full' | 'capped';

/** Complete class strings: Tailwind generates nothing for a name it cannot find whole. */
const WIDTH: Record<NavSearchBarWidth, string> = {
  full: 'w-full',
  capped: 'w-full max-w-md',
};

export function NavSearchBar({ width = 'full' }: { width?: NavSearchBarWidth }) {
  const [searchTerm, setSearchTerm] = useState('');
  const router = useRouter();

  const handleSearch = () => {
    if (searchTerm.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  return (
    <div className={cn('relative', WIDTH[width])}>
      <Input
        type="search"
        placeholder="Search products, stores, and more..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        className="h-10 text-body pr-12 rounded-full"
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
