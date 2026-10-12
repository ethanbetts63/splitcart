import { ResetPasswordForm } from '@/components/forms/reset-password-form';

/**
 * Where the reset email's link lands (`users/notifications.py`).
 *
 * The path is a credential for as long as it lives, so `/reset-password` is
 * disallowed in robots.txt and declared nowhere else -- in particular not
 * noindexed too, which seo-standard.md section 2 forbids: a disallowed page is
 * never fetched, so the directive on it would never be read.
 */
type PageProps = { params: Promise<{ uid: string; token: string }> };

export default async function Page({ params }: PageProps) {
  const { uid, token } = await params;
  return (
    <div className="site-shell py-10 flex justify-center">
      <ResetPasswordForm uid={uid} token={token} className="w-full max-w-panel-wide" />
    </div>
  );
}
