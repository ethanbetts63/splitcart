'use client';

import { SignupForm } from '../components/ui/signup-form';

export default function SignupPage() {
  return (
    <div className="site-shell py-10 flex justify-center">
      <SignupForm className="w-full max-w-lg" />
    </div>
  );
}
