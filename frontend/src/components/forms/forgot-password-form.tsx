'use client';

import Link from 'next/link';
import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';
import { FIELD_MAX } from '@freetheplatform/web-security';
import { Button } from '../common/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../common/card';
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from '../common/field';
import { Input } from '../common/input';
import { Spinner } from '../common/spinner';
import { submitForgotPassword, type ForgotPasswordState } from './forgot-password-form.actions';

const INITIAL: ForgotPasswordState = { status: 'idle' };

export function ForgotPasswordForm(props: React.ComponentProps<typeof Card>) {
  const [state, formAction] = useActionState(submitForgotPassword, INITIAL);

  return (
    <Card {...props}>
      <CardHeader>
        <CardTitle>Reset your password</CardTitle>
        <CardDescription>
          Enter the address you signed up with and we will email you a link to choose a new
          password.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {state.status === 'sent' ? (
          <p className="text-body" role="status">
            If that address has an account, a reset link is on its way. It works once and expires in
            three days.
          </p>
        ) : (
          <form action={formAction}>
            <FieldGroup>
              {state.errors?._form && (
                <div className="rounded-md border border-fill-danger bg-surface-danger p-4 text-body text-text-danger">
                  {state.errors._form.map((message) => (
                    <p key={message}>{message}</p>
                  ))}
                </div>
              )}
              <Field data-invalid={state.errors?.email ? true : undefined}>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  required
                  maxLength={FIELD_MAX.email}
                  autoComplete="email"
                  aria-invalid={state.errors?.email ? true : undefined}
                />
                {state.errors?.email && <FieldError>{state.errors.email[0]}</FieldError>}
              </Field>
              <Field>
                <SubmitButton />
                <FieldDescription className="text-center">
                  Remembered it?{' '}
                  <Link href="/login" className="underline">
                    Sign in
                  </Link>
                </FieldDescription>
              </Field>
            </FieldGroup>
          </form>
        )}
      </CardContent>
    </Card>
  );
}

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending}>
      {pending ? <Spinner /> : 'Email me a link'}
    </Button>
  );
}
