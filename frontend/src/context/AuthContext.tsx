import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  anonymousId: string | null;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [anonymousId, setAnonymousId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = () => {
      setIsLoading(true);
      try {
        const storedToken = localStorage.getItem('token');
        // Read the anonymousId from the cookie set by the backend.
        const storedAnonymousId = document.cookie.split('; ').find(row => row.startsWith('anonymousId='))?.split('=')[1] ?? null;

        if (storedToken) {
          setIsAuthenticated(true);
          setToken(storedToken);
          setAnonymousId(null); // A logged-in user should not use an anonymous ID.
        } else if (storedAnonymousId) {
          setIsAuthenticated(false);
          setToken(null);
          setAnonymousId(storedAnonymousId);
        }
        // If neither exists, the backend will set the anonymousId cookie on the first response.
        // A subsequent page load or context re-render will then pick it up.
      } catch (error) {
        console.error('Failed during auth state initialization:', error);
      } finally {
        setIsLoading(false);
      }
    };

    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener('unauthorized', handleUnauthorized);
    initializeAuth();

    return () => {
      window.removeEventListener('unauthorized', handleUnauthorized);
    };
  }, []);

  const login = (newToken: string) => {
    localStorage.setItem('token', newToken);
    // After logging in, we can remove the anonymousId cookie, though the backend will prioritize the token anyway.
    document.cookie = 'anonymousId=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    setIsAuthenticated(true);
    setToken(newToken);
    setAnonymousId(null);
  };

  const logout = () => {
    localStorage.removeItem('token');
    sessionStorage.clear(); // Clear all session storage for a cleaner logout
    setIsAuthenticated(false);
    setToken(null);
    // The backend will assign a new anonymousId on the next request after reload.
    document.cookie = 'anonymousId=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    setAnonymousId(null);
    window.location.reload(); // Force a full page reload to reset all state.
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, token, anonymousId, isLoading, login, logout }}>
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
