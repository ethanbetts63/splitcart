export interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  anonymousId: string | null;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
}
