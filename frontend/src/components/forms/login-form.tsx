'use client';

import { cn } from '../../lib/utils';
import priceDestroyerImage from '../../assets/price_destroyer.webp';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '../common/button';
import { Card, CardContent } from '../common/card';
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from '../common/field';
import { Input } from '../common/input';
import { useActionState, useEffect, useRef } from 'react';
import { useFormStatus } from 'react-dom';
import { useAuth } from '../../context/AuthContext';
import { Spinner } from '../common/spinner';
import { assetSrc } from '@/lib/assets';
import { FIELD_MAX } from '@freetheplatform/web-security';
import { submitLogin, type LoginState } from './login-form.actions';

const INITIAL: LoginState = { status: 'idle' };

export function LoginForm({ className, ...props }: React.ComponentProps<'div'>) {
  const { refreshSession } = useAuth();
  const router = useRouter();
  const [state, formAction] = useActionState(submitLogin, INITIAL);

  // Every submission returns a new state object, so the ref is what makes this
  // run once per success rather than once per render. The cookies the action
  // relayed are on the browser by now; reading the session flips the cart over
  // to the account, which already holds whatever the signed-out cart held.
  const adopted = useRef<LoginState | null>(null);
  useEffect(() => {
    if (state.status !== 'success' || adopted.current === state) return;
    adopted.current = state;
    void refreshSession().then(() => router.push('/'));
  }, [state, refreshSession, router]);

  return (
    <div className={cn('flex flex-col gap-6', className)} {...props}>
      <Card className="overflow-hidden p-0">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form className="p-6 md:p-8" action={formAction}>
            <FieldGroup>
              <div className="flex flex-col items-center gap-2 text-center">
                <h1 className="text-title-sm font-bold">Welcome back!</h1>
                <p className="text-text-muted text-balance">Login to start hunting bargains!</p>
              </div>
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
                  placeholder="m@example.com"
                  required
                  maxLength={FIELD_MAX.email}
                  autoComplete="email"
                  aria-invalid={state.errors?.email ? true : undefined}
                />
                {state.errors?.email && <FieldError>{state.errors.email[0]}</FieldError>}
              </Field>
              <Field data-invalid={state.errors?.password ? true : undefined}>
                <div className="flex items-center">
                  <FieldLabel htmlFor="password">Password</FieldLabel>
                  <Link
                    href="/forgot-password"
                    className="ml-auto text-body underline-offset-2 hover:underline"
                  >
                    Forgot your password?
                  </Link>
                </div>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  required
                  maxLength={FIELD_MAX.password}
                  autoComplete="current-password"
                  aria-invalid={state.errors?.password ? true : undefined}
                />
                {state.errors?.password && <FieldError>{state.errors.password[0]}</FieldError>}
              </Field>
              <Field>
                <SubmitButton />
              </Field>

              <FieldDescription className="text-center">
                Don&apos;t have an account?{' '}
                <Link href="/signup" className="underline">
                  Sign up
                </Link>
              </FieldDescription>
            </FieldGroup>
          </form>
          <div className="relative hidden md:block">
            <img
              src={assetSrc(priceDestroyerImage)}
              alt="Image"
              className="absolute inset-0 h-full w-full object-contain"
            />
          </div>
        </CardContent>
      </Card>
      <FieldDescription className="px-6 text-center">
        By clicking continue, you agree to our <a href="#">Terms of Service</a> and{' '}
        <a href="#">Privacy Policy</a>.
      </FieldDescription>
    </div>
  );
}

/**
 * Hoisted to module scope: a component declared inside another component's body
 * is a new type on every render, and `useFormStatus` has to be read from a
 * child of the `<form>` regardless.
 */
function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending}>
      {pending ? <Spinner /> : 'Login'}
    </Button>
  );
}
