import { z } from 'zod';

import { email, password } from '@/lib/fieldMax';

/**
 * Track B: flat fields, one submit, one result. Nothing here is repeatable and
 * no rule decides whether another field is required, which is the question
 * FORMS-4 actually asks.
 *
 * `anonymous_id` is not a field of this schema. It is not typed by anybody —
 * it comes from `AuthContext`, is the browser's own identifier, and is
 * validated as a UUID by `CustomLoginSerializer` on the way in. Putting it in
 * the schema would mean parsing a hidden input a page can rewrite.
 */
export const loginSchema = z.object({
  email: email(),
  // An existing credential being typed, not a new one being chosen, so the
  // only floor is "not blank": a minimum here would refuse a password that
  // predates the current rule instead of letting Django say so. The ceiling
  // still applies -- it is what the hasher is asked to chew through.
  password: password(0),
});

export type LoginValues = z.infer<typeof loginSchema>;
