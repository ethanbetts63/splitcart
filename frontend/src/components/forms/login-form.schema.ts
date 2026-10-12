import { z } from 'zod';

import { FIELD_MAX } from '@freetheplatform/web-security';
import { email } from '@freetheplatform/web-security/schema';

/**
 * Track B: flat fields, one submit, one result. Nothing here is repeatable and
 * no rule decides whether another field is required, which is the question
 * FORMS-4 actually asks.
 *
 * `anonymous_id` is not a field of this schema. It is not typed by anybody —
 * the Server Action reads it from the request's own cookie, and Django
 * validates it as a UUID. Putting it in the schema would mean parsing a hidden
 * input a page can rewrite.
 */
export const loginSchema = z.object({
  email: email({ required: 'Enter your email address.' }),
  // An existing credential being typed, not a new one being chosen, so the
  // only floor is "not blank": a minimum here would refuse a password that
  // predates the current rule instead of letting Django say so. The ceiling
  // still applies -- it is what the hasher is asked to chew through.
  password: z.string().min(1, 'Enter your password.').max(FIELD_MAX.password),
});

export type LoginValues = z.infer<typeof loginSchema>;
