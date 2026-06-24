"use client";

import Link from "next/link";
import { Button } from "./ui/button";
import { useAuth } from "@/context/AuthContext";

export function NavAuthButton() {
  const { isAuthenticated, logout } = useAuth();

  if (isAuthenticated) {
    return <Button variant="outline" size="sm" onClick={logout}>Logout</Button>;
  }
  return (
    <Link href="/login">
      <Button variant="outline" size="sm">Login</Button>
    </Link>
  );
}
