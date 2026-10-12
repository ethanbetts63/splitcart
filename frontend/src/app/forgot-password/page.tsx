import { ForgotPasswordForm } from '@/components/forms/forgot-password-form';
import { NOINDEX_METADATA } from '@/lib/pages';

export const metadata = NOINDEX_METADATA;

export default function Page() {
  return (
    <div className="site-shell py-10 flex justify-center">
      <ForgotPasswordForm className="w-full max-w-panel-wide" />
    </div>
  );
}
