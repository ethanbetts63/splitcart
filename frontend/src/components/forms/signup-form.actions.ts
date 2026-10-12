'use server';

import { z } from 'zod';
import { anonymousIdFromCookies } from '@/lib/anonymousId';
import { serverApiFetch } from '@/lib/serverApi';
import { relaySetCookies } from '@/lib/serverCookies';
import { signupSchema } from './signup-form.schema';

type SignupField = 'full_name' | 'email' | 'password1' | 'password2' | '_form';

export interface SignupState {
  status: 'idle' | 'success' | 'error';
  errors?: Partial<Record<SignupField, string[]>>;
}

const GENERIC_FAILURE = 'We could not create your account. Try again.';

/** Django's field errors, kept only where this form has somewhere to show them. */
const SHOWN: readonly SignupField[] = ['full_name', 'email', 'password1', 'password2'];

/**
 * Track B. Registration ends signed in: Django sets the session cookies on its
 * answer and this relays them, the same as login. The signed-out cart rides
 * along as `anonymous_id`.
 */
export async function submitSignup(
  _previous: SignupState,
  formData: FormData,
): Promise<SignupState> {
  const parsed = signupSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { status: 'error', errors: z.flattenError(parsed.error).fieldErrors };
  }

  let response: Response;
  try {
    response = await serverApiFetch('/api/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...parsed.data, anonymous_id: await anonymousIdFromCookies() }),
    });
  } catch {
    return {
      status: 'error',
      errors: { _form: ['We could not reach SplitCart. Check your connection and try again.'] },
    };
  }

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const fields = (typeof body === 'object' && body !== null ? body : {}) as Record<
      string,
      unknown
    >;
    const errors: NonNullable<SignupState['errors']> = {};
    for (const field of SHOWN) {
      const messages = fields[field];
      if (Array.isArray(messages)) errors[field] = messages.map(String);
    }
    // Anything Django rejected that this form has no field for still has to
    // reach the person: a silent 400 reads as a button that does nothing.
    const unplaced = Object.entries(fields)
      .filter(([field]) => !SHOWN.includes(field as SignupField))
      .flatMap(([, messages]) => (Array.isArray(messages) ? messages.map(String) : []));
    if (unplaced.length || !Object.keys(errors).length) {
      errors._form = unplaced.length ? unplaced : [GENERIC_FAILURE];
    }
    return { status: 'error', errors };
  }

  await relaySetCookies(response);
  return { status: 'success' };
}
