'use client';

import { Button } from './button';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from './field';
import { Input } from './input';
import { useActionState, useEffect, useRef } from 'react';
import { useFormStatus } from 'react-dom';
import { z } from 'zod';
import { useAuth } from '../../context/AuthContext';
import { Spinner } from './spinner';
import { getApiUrl } from '@/lib/apiUrl';
import { FIELD_MAX } from '@/lib/fieldMax';
import { MINIMUM_PASSWORD_LENGTH, signupSchema } from './signup-form.schema';

/**
 * Track B, in the shape this app can hold today -- see the note in
 * `login-form.tsx` for why this is a client action rather than a Server Action,
 * and `_docs/convergence/auth-migration.md` for when it stops being one.
 *
 * The confirm-password rule moved out of `handleSubmit` and into the schema's
 * `.refine()`. It was the only validation this form had.
 */
type SignupField = 'full_name' | 'email' | 'password1' | 'password2' | '_form';

interface SignupState {
  errors?: Partial<Record<SignupField, string[]>>;
  /** The DRF token, present only on the render that follows a success. */
  token?: string;
}

const GENERIC_FAILURE = 'We could not create your account. Try again.';

/** Django's field errors, kept only where this form has somewhere to show them. */
const SHOWN: readonly SignupField[] = ['full_name', 'email', 'password1', 'password2'];

async function submitSignup(
  anonymousId: string | null,
  _previous: SignupState,
  formData: FormData,
): Promise<SignupState> {
  const parsed = signupSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { errors: z.flattenError(parsed.error).fieldErrors };
  }

  let response: Response;
  try {
    response = await fetch(getApiUrl('/api/auth/registration/'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // `anonymous_id` hands the signed-out cart to the account being created,
      // the way logging in already does. `CustomRegisterSerializer` validates
      // it and runs the same merge.
      body: JSON.stringify({ ...parsed.data, anonymous_id: anonymousId }),
    });
  } catch {
    return {
      errors: { _form: ['We could not reach SplitCart. Check your connection and try again.'] },
    };
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const errors: NonNullable<SignupState['errors']> = {};
    for (const field of SHOWN) {
      if (Array.isArray(body?.[field])) errors[field] = body[field];
    }
    // Anything Django rejected that this form has no field for still has to
    // reach the person: a silent 400 reads as a button that does nothing.
    const unplaced = Object.entries(body ?? {})
      .filter(([field]) => !SHOWN.includes(field as SignupField))
      .flatMap(([, messages]) => (Array.isArray(messages) ? (messages as string[]) : []));
    if (unplaced.length || !Object.keys(errors).length) {
      errors._form = unplaced.length ? unplaced : [GENERIC_FAILURE];
    }
    return { errors };
  }
  return { token: body?.key };
}

export function SignupForm({ ...props }: React.ComponentProps<typeof Card>) {
  const { login, anonymousId } = useAuth();
  const router = useRouter();
  const [state, formAction] = useActionState(submitSignup.bind(null, anonymousId), {});

  // See `login-form.tsx`: `login` changes identity on every provider render, so
  // the ref is what makes this run once per token instead of once per render.
  const adopted = useRef<string | null>(null);
  useEffect(() => {
    if (!state.token || adopted.current === state.token) return;
    adopted.current = state.token;
    login(state.token);
    router.push('/');
  }, [state.token, login, router]);

  return (
    <Card {...props}>
      <CardHeader>
        <CardTitle>Create an account</CardTitle>
        <CardDescription>
          Enter your information below to create your account. We take
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form action={formAction}>
          <FieldGroup>
            {state.errors?._form && (
              <div className="rounded-md border border-fill-danger bg-surface-danger p-4 text-body text-text-danger">
                {state.errors._form.map((message) => (
                  <p key={message}>{message}</p>
                ))}
              </div>
            )}
            <Field data-invalid={state.errors?.full_name ? true : undefined}>
              <FieldLabel htmlFor="name">Full Name</FieldLabel>
              <Input
                id="name"
                name="full_name"
                type="text"
                placeholder="John Doe"
                required
                maxLength={FIELD_MAX.name}
                autoComplete="name"
                aria-invalid={state.errors?.full_name ? true : undefined}
              />
              {state.errors?.full_name && <FieldError>{state.errors.full_name[0]}</FieldError>}
            </Field>
            <Field data-invalid={state.errors?.email ? true : undefined}>
              <FieldLabel htmlFor="email">Email</FieldLabel>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="m@example.com"
                required
                maxLength={FIELD_MAX.email}
                autoComplete="email"
                aria-invalid={state.errors?.email ? true : undefined}
              />
              {state.errors?.email ? (
                <FieldError>{state.errors.email[0]}</FieldError>
              ) : (
                <FieldDescription>
                  We&apos;ll use this to contact you. We will not share your email with anyone else.
                </FieldDescription>
              )}
            </Field>
            <Field data-invalid={state.errors?.password1 ? true : undefined}>
              <FieldLabel htmlFor="password">Password</FieldLabel>
              <Input
                id="password"
                name="password1"
                type="password"
                required
                maxLength={FIELD_MAX.password}
                autoComplete="new-password"
                aria-invalid={state.errors?.password1 ? true : undefined}
              />
              {state.errors?.password1 ? (
                <FieldError>{state.errors.password1.join(' ')}</FieldError>
              ) : (
                <FieldDescription>
                  Must be at least {MINIMUM_PASSWORD_LENGTH} characters long.
                </FieldDescription>
              )}
            </Field>
            <Field data-invalid={state.errors?.password2 ? true : undefined}>
              <FieldLabel htmlFor="confirm-password">Confirm Password</FieldLabel>
              <Input
                id="confirm-password"
                name="password2"
                type="password"
                required
                maxLength={FIELD_MAX.password}
                autoComplete="new-password"
                aria-invalid={state.errors?.password2 ? true : undefined}
              />
              {state.errors?.password2 && (
                <FieldError>{state.errors.password2.join(' ')}</FieldError>
              )}
            </Field>
            <FieldGroup>
              <Field>
                <SubmitButton />
                <FieldDescription className="px-6 text-center">
                  Already have an account?{' '}
                  <Link href="/login" className="underline">
                    Sign in
                  </Link>
                </FieldDescription>
              </Field>
            </FieldGroup>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}

/** Module scope, so it is one component type rather than a new one per render. */
function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending}>
      {pending ? <Spinner /> : 'Create Account'}
    </Button>
  );
}
