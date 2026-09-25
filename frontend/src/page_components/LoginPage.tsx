'use client';

import { LoginForm } from '../components/ui/login-form';

export default function LoginPage() {
  return (
    <div className="site-shell py-10 flex justify-center">
      <LoginForm className="w-full max-w-2xl" />
    </div>
  );
}
