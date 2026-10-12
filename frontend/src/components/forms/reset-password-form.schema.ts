import { z } from 'zod';

import { FIELD_MAX } from '@freetheplatform/web-security';
import { password } from '@freetheplatform/web-security/schema';

import { MINIMUM_PASSWORD_LENGTH } from './signup-form.schema';

/**
 * Track B. The confirm field is the standard's own carve-out: one rule over two
 * adjacent fields. `uid` and `token` are not fields -- they come from the link's
 * path and are bound to the action, never typed and never a hidden input.
 */
export const resetPasswordSchema = z
  .object({
    new_password: password(MINIMUM_PASSWORD_LENGTH),
    confirm_password: z.string().max(FIELD_MAX.password),
  })
  .refine((values) => values.new_password === values.confirm_password, {
    message: 'Those two passwords do not match.',
    path: ['confirm_password'],
  });
