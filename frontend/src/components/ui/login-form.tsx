'use client';

import { cn } from '../../lib/utils';
import priceDestroyerImage from '../../assets/price_destroyer.webp';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from './button';
import { Card, CardContent } from './card';
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from './field';
import { Input } from './input';
import { useActionState, useEffect, useRef } from 'react';
import { useFormStatus } from 'react-dom';
import { z } from 'zod';
import { useAuth } from '../../context/AuthContext';
import { Spinner } from './spinner';
import { assetSrc } from '@/lib/assets';
import { getApiUrl } from '@/lib/apiUrl';
import { FIELD_MAX } from '@/lib/fieldMax';
import { loginSchema } from './login-form.schema';

/**
 * Track B, in the shape this app can actually hold today.
 *
 * `forms-standard.md` wires Track B to a Server Action. splitcart has none, and
 * cannot have one here: the thing login produces is a DRF token that lives in
 * `localStorage` and is attached by client JavaScript on every later request,
 * so there is no session for a Next server to establish. FORMS-9/10/11 are
 * `n/a` for that reason, not unimplemented -- see
 * `_docs/convergence/auth-migration.md`, which is where the session model
 * changes and this becomes a real `'use server'` action.
 *
 * Everything else is the standard's Track B verbatim: `useActionState` over an
 * action that parses `FormData` against the schema beside this file, returns
 * field errors on failure, and otherwise calls Django once.
 */
interface LoginState {
  errors?: Partial<Record<'email' | 'password' | '_form', string[]>>;
  /** The DRF token, present only on the render that follows a success. */
  token?: string;
}

const GENERIC_FAILURE = 'We could not sign you in. Check your details and try again.';

async function submitLogin(
  anonymousId: string | null,
  _previous: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const parsed = loginSchema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  });
  if (!parsed.success) {
    return { errors: z.flattenError(parsed.error).fieldErrors };
  }

  let response: Response;
  try {
    response = await fetch(getApiUrl('/api/auth/login/'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...parsed.data, anonymous_id: anonymousId }),
    });
  } catch {
    return {
      errors: { _form: ['We could not reach SplitCart. Check your connection and try again.'] },
    };
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    return { errors: { _form: [body?.non_field_errors?.[0] ?? GENERIC_FAILURE] } };
  }
  return { token: body?.key };
}

export function LoginForm({ className, ...props }: React.ComponentProps<'div'>) {
  const { login, anonymousId } = useAuth();
  const router = useRouter();
  const [state, formAction] = useActionState(submitLogin.bind(null, anonymousId), {});

  // `login` is re-created on every `AuthProvider` render, so it cannot gate
  // this effect on its own -- the ref is what makes the effect run once per
  // token rather than once per render.
  const adopted = useRef<string | null>(null);
  useEffect(() => {
    if (!state.token || adopted.current === state.token) return;
    adopted.current = state.token;
    login(state.token);
    router.push('/');
  }, [state.token, login, router]);

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
                  <a href="#" className="ml-auto text-body underline-offset-2 hover:underline">
                    Forgot your password?
                  </a>
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
