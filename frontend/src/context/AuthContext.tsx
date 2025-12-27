import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { performInitialSetupAPI } from '../services/auth.api';
import { type Cart, type SelectedStoreListType } from '../types';
import { type AnchorMap } from './StoreListContext';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  anonymousId: string | null;
  initialCart: Cart | null;
  initialStoreList: SelectedStoreListType | null;
  initialAnchorMap: AnchorMap | null;
  isLoading: boolean; // New loading state
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [anonymousId, setAnonymousId] = useState<string | null>(null);
  const [initialAnchorMap, setInitialAnchorMap] = useState<AnchorMap | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Add loading state
  const [initialCart, setInitialCart] = useState<Cart | null>(() => ({
    id: 'local',
    name: 'Shopping Cart',
    is_active: true,
    items: [],
    selected_store_list: {
      id: 'local-store-list',
      name: 'My Stores',
      stores: [],
      is_user_defined: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_used_at: new Date().toISOString(),
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }));
  const [initialStoreList, setInitialStoreList] = useState<SelectedStoreListType | null>(() => ({
    id: 'local',
    name: 'My Stores',
    stores: [],
    is_user_defined: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    last_used_at: new Date().toISOString(),
  }));

  useEffect(() => {
    const initializeUser = async () => {
      setIsLoading(true);
      try {
        // Call the API directly, no longer relying on a pre-fetched promise.
        const initialData = await performInitialSetupAPI(null, null);

        if (initialData.error) {
            throw new Error(`Initial data fetch failed with status: ${initialData.status}`);
        }

        const storedToken = localStorage.getItem('token');
        if (storedToken) {
          setIsAuthenticated(true);
          setToken(storedToken);
        }

        if (initialData.anonymous_id) {
          document.cookie = `anonymousId=${initialData.anonymous_id}; path=/; max-age=31536000;`; // 1 year expiry
          setAnonymousId(initialData.anonymous_id);
        }

        setInitialCart(initialData.cart);
        setInitialStoreList(initialData.cart.selected_store_list ?? null);
        setInitialAnchorMap(initialData.anchor_map ?? null);

      } catch (error) {
        console.error('Failed during initial user setup:', error);
        // On failure, we still have the initial local state.
      } finally {
        setIsLoading(false); // Set loading to false after success or failure
      }
    };

    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener('unauthorized', handleUnauthorized);
    initializeUser();

    return () => {
      window.removeEventListener('unauthorized', handleUnauthorized);
    };
  }, []);

  const login = (newToken: string) => {
    localStorage.setItem('token', newToken);
    setIsAuthenticated(true);
    setToken(newToken);
    // Clear anonymousId on login
    document.cookie = 'anonymousId=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    setAnonymousId(null);
  };

  const logout = () => {
    localStorage.removeItem('token');
    sessionStorage.removeItem('selectedStoreIds'); // Clear selected stores from session storage
    sessionStorage.removeItem('postcode'); // Clear postcode from session storage
    sessionStorage.removeItem('stores'); // Clear stores from session storage
    setIsAuthenticated(false);
    setToken(null);
    // Clear anonymousId on logout
    document.cookie = 'anonymousId=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    setAnonymousId(null);
    window.location.reload(); // Force a full page reload to reset all state
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, token, anonymousId, initialCart, initialStoreList, initialAnchorMap, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
