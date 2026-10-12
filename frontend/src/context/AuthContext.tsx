import { apiFetch } from '@freetheplatform/web-security';
import { createContext, useCallback, useContext, useState, useEffect, type ReactNode } from 'react';
import type { AuthContextType, Principal } from '../types/AuthContextType';
import { AUTH_FAILURE_EVENT, tryRefreshSession } from '@/services/apiClient';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ANONYMOUS_COOKIE = 'anonymousId';

const createAnonymousId = () => {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const readAnonymousId = () =>
  document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${ANONYMOUS_COOKIE}=`))
    ?.split('=')[1] ?? null;

const persistAnonymousId = (anonymousId: string) => {
  const secure = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `${ANONYMOUS_COOKIE}=${encodeURIComponent(anonymousId)}; max-age=31536000; path=/; SameSite=Lax${secure}`;
};

const forgetAnonymousId = () => {
  document.cookie = `${ANONYMOUS_COOKIE}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
};

/**
 * Who the session cookies belong to, or `null` for a signed-out browser.
 *
 * The cookies are HttpOnly, so the only way to know is to ask. An expired
 * access token is normal on a first load -- the refresh token outlives it by
 * days -- so a 401 is answered with one quiet refresh rather than the
 * auth-failure cascade, which is for a session that ends mid-use.
 */
const readPrincipal = async (): Promise<Principal | null> => {
  try {
    let response = await apiFetch('/api/me/');
    if (response.status === 401 && (await tryRefreshSession())) {
      response = await apiFetch('/api/me/');
    }
    return response.ok ? ((await response.json()) as Principal) : null;
  } catch {
    // Unreachable API: browse signed out rather than not at all.
    return null;
  }
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [principal, setPrincipal] = useState<Principal | null>(null);
  const [anonymousId, setAnonymousId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Sets state from what the session turned out to be. A signed-in shopper
   * carries no anonymous ID -- the cart it named was handed to the account at
   * the door -- and a signed-out one always has one, minted here if the
   * browser has none yet.
   */
  const adopt = useCallback((next: Principal | null) => {
    setPrincipal(next);
    if (next) {
      forgetAnonymousId();
      setAnonymousId(null);
      return;
    }
    let id = readAnonymousId();
    if (!id) {
      id = createAnonymousId();
      persistAnonymousId(id);
    }
    setAnonymousId(id);
  }, []);

  const refreshSession = useCallback(async () => {
    adopt(await readPrincipal());
  }, [adopt]);

  /**
   * Revokes on the server, then starts over. The POST is what makes signing out
   * a containment step: the refresh token is blacklisted, not merely forgotten
   * by this browser. Logout always answers 200, so there is nothing to handle.
   */
  const logout = useCallback(async () => {
    await apiFetch('/api/token/logout/', { method: 'POST' }).catch(() => undefined);
    sessionStorage.clear();
    forgetAnonymousId();
    window.location.reload();
  }, []);

  useEffect(() => {
    let cancelled = false;
    void readPrincipal().then((next) => {
      if (cancelled) return;
      adopt(next);
      setIsLoading(false);
    });

    // The shared fetch fires this when a refresh fails mid-use: the session is
    // over, so the page starts again signed out.
    const handleAuthFailure = () => void logout();
    window.addEventListener(AUTH_FAILURE_EVENT, handleAuthFailure);
    return () => {
      cancelled = true;
      window.removeEventListener(AUTH_FAILURE_EVENT, handleAuthFailure);
    };
  }, [adopt, logout]);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: principal !== null,
        principal,
        anonymousId,
        isLoading,
        refreshSession,
        logout,
      }}
    >
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
