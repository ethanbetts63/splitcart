'use client';

import { Button } from '../common/button';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../common/card';
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from '../common/field';
import { Input } from '../common/input';
import { useActionState, useEffect, useRef } from 'react';
import { useFormStatus } from 'react-dom';
import { useAuth } from '../../context/AuthContext';
import { Spinner } from '../common/spinner';
import { FIELD_MAX } from '@freetheplatform/web-security';
import { MINIMUM_PASSWORD_LENGTH } from './signup-form.schema';
import { submitSignup, type SignupState } from './signup-form.actions';

const INITIAL: SignupState = { status: 'idle' };

export function SignupForm({ ...props }: React.ComponentProps<typeof Card>) {
  const { refreshSession } = useAuth();
  const router = useRouter();
  const [state, formAction] = useActionState(submitSignup, INITIAL);

  // See `login-form.tsx`: once per success, not once per render.
  const adopted = useRef<SignupState | null>(null);
  useEffect(() => {
    if (state.status !== 'success' || adopted.current === state) return;
    adopted.current = state;
    void refreshSession().then(() => router.push('/'));
  }, [state, refreshSession, router]);

  return (
    <Card {...props}>
      <CardHeader>
        <CardTitle>Create an account</CardTitle>
        <CardDescription>Enter your information below to create your account.</CardDescription>
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
