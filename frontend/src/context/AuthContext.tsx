import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { performInitialSetupAPI, type InitialSetupData } from '@/services/initialSetupApi';
import { type Cart } from '@/types';
import { type SelectedStoreListType } from '@/context/StoreListContext';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  anonymousId: string | null;
  initialCart: Cart | null;
  initialStoreList: SelectedStoreListType | null;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [anonymousId, setAnonymousId] = useState<string | null>(null);
  const [initialCart, setInitialCart] = useState<Cart | null>(null);
  const [initialStoreList, setInitialStoreList] = useState<SelectedStoreListType | null>(null);

  useEffect(() => {
    const initializeUser = async () => {
            const storedToken = localStorage.getItem('token') ?? null;
            const storedAnonymousId = localStorage.getItem('anonymousId') ?? null;

      let currentToken = storedToken;
      let currentAnonymousId = storedAnonymousId;

      if (currentToken) {
        setIsAuthenticated(true);
        setToken(currentToken);
        if (currentAnonymousId) {
          document.cookie = 'anonymousId=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
          setAnonymousId(null);
          currentAnonymousId;
        }
      } else if (currentAnonymousId) {
        setAnonymousId(currentAnonymousId);
      } else {
        try {
          const response = await fetch('/api/anonymous-user/', { method: 'POST' });
          if (response.ok) {
            const data = await response.json();
            document.cookie = `anonymousId=${data.anonymous_id}; path=/; max-age=31536000;`; // 1 year expiry
            setAnonymousId(data.anonymous_id);
            currentAnonymousId = data.anonymous_id;
          }
        } catch (error) {
          console.error('Failed to create anonymous user:', error);
        }
      }

      // Perform initial setup if we have a token or an anonymousId
      if (currentToken || currentAnonymousId) {
        try {
          const initialData = await performInitialSetupAPI(currentToken, currentAnonymousId);
          setInitialCart(initialData.cart);
          setInitialStoreList(initialData.store_list);
        } catch (error) {
          console.error('Failed to perform initial setup:', error);
        }
      }
    };

    initializeUser();
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
    <AuthContext.Provider value={{ isAuthenticated, token, anonymousId, initialCart, initialStoreList, login, logout }}>
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
