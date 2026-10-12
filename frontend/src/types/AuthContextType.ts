/** What `/api/me/` and a successful login answer with. See `users/principal.py`. */
export interface Principal {
  id: number;
  email: string;
  full_name: string;
  role: 'shopper';
  must_change_password: boolean;
}

export interface AuthContextType {
  isAuthenticated: boolean;
  principal: Principal | null;
  anonymousId: string | null;
  isLoading: boolean;
  /** Re-read the session after something outside this context changed it: a sign-in or sign-up. */
  refreshSession: () => Promise<void>;
  logout: () => Promise<void>;
}
