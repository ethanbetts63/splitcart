'use server';

import { z } from 'zod';
import { serverApiFetch } from '@/lib/serverApi';
import { forgotPasswordSchema } from './forgot-password-form.schema';

export interface ForgotPasswordState {
  status: 'idle' | 'sent' | 'error';
  errors?: Partial<Record<'email' | '_form', string[]>>;
}

/**
 * Asks Django to email a reset link. Django answers the same for an address
 * with an account and one without, and so does this: "sent" never says which.
 */
export async function submitForgotPassword(
  _previous: ForgotPasswordState,
  formData: FormData,
): Promise<ForgotPasswordState> {
  const parsed = forgotPasswordSchema.safeParse({ email: formData.get('email') });
  if (!parsed.success) {
    return { status: 'error', errors: z.flattenError(parsed.error).fieldErrors };
  }

  try {
    const response = await serverApiFetch('/api/password/reset/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed.data),
    });
    if (response.status === 429) {
      return {
        status: 'error',
        errors: { _form: ['Too many requests. Wait a while and try again.'] },
      };
    }
  } catch {
    return {
      status: 'error',
      errors: { _form: ['We could not reach SplitCart. Check your connection and try again.'] },
    };
  }
  return { status: 'sent' };
}
