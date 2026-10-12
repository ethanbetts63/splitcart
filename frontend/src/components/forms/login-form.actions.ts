'use server';

import { z } from 'zod';
import { anonymousIdFromCookies } from '@/lib/anonymousId';
import { serverApiFetch } from '@/lib/serverApi';
import { relaySetCookies } from '@/lib/serverCookies';
import { loginSchema } from './login-form.schema';

export interface LoginState {
  status: 'idle' | 'success' | 'error';
  /** Per field, plus `_form` for a failure that belongs to no one field. */
  errors?: Partial<Record<'email' | 'password' | '_form', string[]>>;
}

const GENERIC_FAILURE = 'We could not sign you in. Check your details and try again.';
const THROTTLED = 'Too many attempts. Wait a minute and try again.';
const UNREACHABLE = 'We could not reach SplitCart. Check your connection and try again.';

/**
 * Track B: parse, call Django once, relay its cookies onto the browser.
 *
 * The session cookies are HttpOnly and set by Django, so the response is never
 * read for a token -- there is none in it. The signed-out cart rides along as
 * `anonymous_id` and is handed to the account if the password is right.
 */
export async function submitLogin(_previous: LoginState, formData: FormData): Promise<LoginState> {
  const parsed = loginSchema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  });
  if (!parsed.success) {
    return { status: 'error', errors: z.flattenError(parsed.error).fieldErrors };
  }

  let response: Response;
  try {
    response = await serverApiFetch('/api/token/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...parsed.data, anonymous_id: await anonymousIdFromCookies() }),
    });
  } catch {
    return { status: 'error', errors: { _form: [UNREACHABLE] } };
  }

  // Form-level, not under either field: saying which one was wrong would tell
  // a stranger whether an address has an account.
  if (!response.ok) {
    return {
      status: 'error',
      errors: { _form: [response.status === 429 ? THROTTLED : GENERIC_FAILURE] },
    };
  }

  await relaySetCookies(response);
  return { status: 'success' };
}
