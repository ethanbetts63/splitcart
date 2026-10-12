import { z } from 'zod';

import { FIELD_MAX } from '@freetheplatform/web-security';
import { email, password, requiredString } from '@freetheplatform/web-security/schema';

/**
 * Django's `MinimumLengthValidator`, restated. The server is still the thing
 * that enforces it -- `AUTH_PASSWORD_VALIDATORS` also runs the similarity and
 * common-password checks, which no schema can do -- and this only saves a
 * round trip for the one failure a person hits most.
 */
export const MINIMUM_PASSWORD_LENGTH = 8;

/**
 * Track B. The `.refine()` is a confirm-field match, which the standard's own
 * carve-out puts outside the cross-field question: it is one rule over two
 * adjacent fields, not a rule deciding whether some *other* field is required.
 *
 * Field names are the wire names, so `Object.fromEntries(formData)` parses
 * straight into the body `/api/register/` expects.
 */
export const signupSchema = z
  .object({
    full_name: requiredString('name', 'Enter your name.'),
    email: email({ required: 'Enter your email address.' }),
    password1: password(MINIMUM_PASSWORD_LENGTH),
    // Bounded but not length-checked: whether it is long enough is decided by
    // the field above, and a second "too short" under the confirm box is noise.
    password2: z.string().max(FIELD_MAX.password),
  })
  .refine((values) => values.password1 === values.password2, {
    message: 'Those two passwords do not match.',
    path: ['password2'],
  });

export type SignupValues = z.infer<typeof signupSchema>;
