import { z } from 'zod';

import { email } from '@freetheplatform/web-security/schema';

/** Track B: one field, one submit. */
export const forgotPasswordSchema = z.object({
  email: email({ required: 'Enter your email address.' }),
});
