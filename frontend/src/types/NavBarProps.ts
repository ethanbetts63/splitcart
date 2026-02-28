import type { KeyboardEvent } from 'react';

export interface NavBarProps {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  handleSearch: () => void;
  handleSearchKeyDown: (event: KeyboardEvent<HTMLInputElement>) => void;
  openDialog: (page: string) => void;
  cartTotal: number;
  selectedStoreIds: Set<number>;
  isUserDefinedList: boolean;
  isAuthenticated: boolean;
  logout: () => void;
}
