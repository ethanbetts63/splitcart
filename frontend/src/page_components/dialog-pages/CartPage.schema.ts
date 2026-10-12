import { z } from 'zod';

import { requiredString } from '@freetheplatform/web-security/schema';

/**
 * Track B: one field, one submit.
 *
 * A cart's name is a label typed on one line, so it is the `line` kind -- the
 * same ceiling `CartRenameSerializer` gives `new_name`, which is what makes the
 * schema and the serializer bound the same field from opposite ends (FORMS-6).
 *
 * `cart_id` is not a field of this schema: it is the active cart's id, read
 * from `CartContext`, never typed. A hidden input carrying it would be a cart
 * id the page could rewrite, and the server would then have to decide whether
 * to believe it.
 */
export const cartRenameSchema = z.object({
  new_name: requiredString('line', 'Give the cart a name.'),
});

export type CartRenameValues = z.infer<typeof cartRenameSchema>;
