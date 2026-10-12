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
import { MINIMUM_PASSWORD_LENGTH } from './signup-form.schema';
import { submitResetPassword, type ResetPasswordState } from './reset-password-form.actions';

const INITIAL: ResetPasswordState = { status: 'idle' };

interface ResetPasswordFormProps extends React.ComponentProps<typeof Card> {
  uid: string;
  token: string;
}

export function ResetPasswordForm({ uid, token, ...props }: ResetPasswordFormProps) {
  const [state, formAction] = useActionState(submitResetPassword.bind(null, uid, token), INITIAL);

  return (
    <Card {...props}>
      <CardHeader>
        <CardTitle>Choose a new password</CardTitle>
        <CardDescription>Every other place you are signed in will be signed out.</CardDescription>
      </CardHeader>
      <CardContent>
        {state.status === 'done' ? (
          <p className="text-body" role="status">
            Your password is changed.{' '}
            <Link href="/login" className="underline">
              Sign in with it
            </Link>
            .
          </p>
        ) : (
          <form action={formAction}>
            <FieldGroup>
              {state.errors?._form && (
                <div className="rounded-md border border-fill-danger bg-surface-danger p-4 text-body text-text-danger">
                  {state.errors._form.map((message) => (
                    <p key={message}>{message}</p>
                  ))}
                  <p>
                    <Link href="/forgot-password" className="underline">
                      Ask for a new link
                    </Link>
                  </p>
                </div>
              )}
              <Field data-invalid={state.errors?.new_password ? true : undefined}>
                <FieldLabel htmlFor="new-password">New password</FieldLabel>
                <Input
                  id="new-password"
                  name="new_password"
                  type="password"
                  required
                  maxLength={FIELD_MAX.password}
                  autoComplete="new-password"
                  aria-invalid={state.errors?.new_password ? true : undefined}
                />
                {state.errors?.new_password ? (
                  <FieldError>{state.errors.new_password.join(' ')}</FieldError>
                ) : (
                  <FieldDescription>
                    Must be at least {MINIMUM_PASSWORD_LENGTH} characters long.
                  </FieldDescription>
                )}
              </Field>
              <Field data-invalid={state.errors?.confirm_password ? true : undefined}>
                <FieldLabel htmlFor="confirm-password">Confirm new password</FieldLabel>
                <Input
                  id="confirm-password"
                  name="confirm_password"
                  type="password"
                  required
                  maxLength={FIELD_MAX.password}
                  autoComplete="new-password"
                  aria-invalid={state.errors?.confirm_password ? true : undefined}
                />
                {state.errors?.confirm_password && (
                  <FieldError>{state.errors.confirm_password.join(' ')}</FieldError>
                )}
              </Field>
              <Field>
                <SubmitButton />
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
      {pending ? <Spinner /> : 'Set password'}
    </Button>
  );
}
