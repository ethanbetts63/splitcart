'use client';

import Link from 'next/link';
import { Button } from './common/button';
import { useAuth } from '@/context/AuthContext';

export function NavAuthButton() {
  const { isAuthenticated, logout } = useAuth();

  if (isAuthenticated) {
    return (
      <Button variant="outline" size="sm" onClick={() => void logout()}>
        Logout
      </Button>
    );
  }
  return (
    // One control, not a button inside a link: that was two tab stops and a
    // nested interactive element for one action.
    <Button asChild variant="outline" size="sm">
      <Link href="/login">Login</Link>
    </Button>
  );
}
