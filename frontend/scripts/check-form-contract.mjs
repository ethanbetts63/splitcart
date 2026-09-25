#!/usr/bin/env node
/**
 * Thin entry point over `scripts/forms/serializer-contract.mjs`. The engine
 * explains the failure it prevents; the pairs below are the repo facts, and
 * the exception rows are where somebody has to say in words why a field the
 * API accepts is one the client never sends.
 *
 * Why this is not folded into `check:forms`. `check:forms` is named by
 * `freetheplatform/_docs/forms-standard.md` and asserts the same ledger and
 * hygiene rules in all four repositories, with nothing but Node behind it.
 * This check crosses into Django: it runs `venv/Scripts/python` to import the
 * serializers, so it fails on a clone with no venv. Bolting that onto the
 * shared command would make splitcart's `check:forms` mean something different
 * from everyone else's. It is a separate row in `npm run check` instead.
 *
 * All three of the repository's Track B forms are here, which is what makes
 * `check:forms`' ledger and this file checkable against each other by eye: the
 * same three files, on the same three endpoints.
 */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkSerializerContract } from './forms/serializer-contract.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

await checkSerializerContract({
  root,
  pairs: [
    {
      endpoint: 'POST /api/auth/login/',
      form: 'components/ui/login-form.tsx',
      schema: { module: 'components/ui/login-form.schema.ts', export: 'loginSchema' },
      serializer: 'users.serializers.custom_login_serializer.CustomLoginSerializer',
      alsoPosts: [
        {
          field: 'anonymous_id',
          why: "The browser's own identifier, read from AuthContext and added to the body rather than typed into the schema. A hidden input would be a value the page could rewrite; CustomLoginSerializer validates it as a UUID either way.",
        },
      ],
      serverOnly: [
        {
          field: 'username',
          why: "dj-rest-auth's second spelling of the identifier. USERNAME_FIELD is `email` for this project's user, so the serializer bounds `username` for the same reason it bounds `email` and the form has one field, not two.",
        },
      ],
    },
    {
      endpoint: 'POST /api/auth/registration/',
      form: 'components/ui/signup-form.tsx',
      schema: { module: 'components/ui/signup-form.schema.ts', export: 'signupSchema' },
      serializer: 'users.serializers.custom_register_serializer.CustomRegisterSerializer',
      alsoPosts: [
        {
          field: 'anonymous_id',
          why: 'Same value, same reason as login. This is the field whose absence lost the signed-out cart on every signup until CustomRegisterSerializer.save() started merging it.',
        },
      ],
      serverOnly: [
        {
          field: 'username',
          why: "Inherited from dj-rest-auth's RegisterSerializer and optional because ACCOUNT_USERNAME_REQUIRED is off: this project's user has no username column. Nothing should start sending one.",
        },
      ],
    },
    {
      endpoint: 'POST /api/carts/rename/',
      form: 'page_components/dialog-pages/CartPage.tsx',
      schema: {
        module: 'page_components/dialog-pages/CartPage.schema.ts',
        export: 'cartRenameSchema',
      },
      serializer: 'users.serializers.cart_action_serializers.CartRenameSerializer',
      alsoPosts: [
        {
          field: 'cart_id',
          // Not the form file: the rename goes out through `renameCart`, which
          // is where the id joins the body.
          in: 'services/cart.api.ts',
          why: "The active cart's id, read from CartContext and never typed. A hidden input carrying it would be an id the page could rewrite, and the server would then have to decide whether to believe it.",
        },
      ],
    },
  ],
});
