'use server';

import { z } from 'zod';
import { serverApiFetch } from '@/lib/serverApi';
import { resetPasswordSchema } from './reset-password-form.schema';

export interface ResetPasswordState {
  status: 'idle' | 'done' | 'error';
  errors?: Partial<Record<'new_password' | 'confirm_password' | '_form', string[]>>;
}

/**
 * Spends the link on a new password. Django signs nobody in here: reading an
 * account's email is not the same as being signed in, so the next step is the
 * login form.
 */
export async function submitResetPassword(
  uid: string,
  token: string,
  _previous: ResetPasswordState,
  formData: FormData,
): Promise<ResetPasswordState> {
  const parsed = resetPasswordSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { status: 'error', errors: z.flattenError(parsed.error).fieldErrors };
  }

  let response: Response;
  try {
    response = await serverApiFetch('/api/password/reset/confirm/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid, token, new_password: parsed.data.new_password }),
    });
  } catch {
    return {
      status: 'error',
      errors: { _form: ['We could not reach SplitCart. Check your connection and try again.'] },
    };
  }
  if (response.ok) return { status: 'done' };

  // `new_password` carries the validators' reasons; `detail` is one sentence
  // for an expired, spent or forged link alike.
  const body = (await response.json().catch(() => null)) as {
    new_password?: unknown;
    detail?: unknown;
  } | null;
  if (Array.isArray(body?.new_password)) {
    return { status: 'error', errors: { new_password: body.new_password.map(String) } };
  }
  return {
    status: 'error',
    errors: {
      _form: [
        typeof body?.detail === 'string' ? body.detail : 'This reset link is no longer valid.',
      ],
    },
  };
}
