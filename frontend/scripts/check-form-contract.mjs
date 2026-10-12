#!/usr/bin/env node
/**
 * Thin entry point over `scripts/forms/serializer-contract.mjs`, a registry
 * copy — edit it in `freetheplatform/frontend/registry/tooling/forms/`. The engine
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
 * Every Track B form in `check:forms`' ledger is here but one, and the two
 * lists are meant to be checked against each other by eye. The forgot-password
 * form posts to a serializer in `freetheplatform.auth`, which this repository
 * installs and so can import like its own.
 *
 * The one absent is `reset-password-form.tsx`. Its body is assembled in the
 * action rather than posted from the controls -- `uid` and `token` come from the
 * link's path, and `confirm_password` is checked by the schema and never sent --
 * so the engine's reading of control names as the posted body does not hold for
 * it. Its serializer is the package's `PasswordResetConfirmSerializer`, and the
 * action names its three fields literally.
 */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkSerializerContract } from './forms/serializer-contract.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

await checkSerializerContract({
  root,
  // `config.settings` with SQLite: the module the Python suite runs under.
  settingsModule: 'settings_test',
  pairs: [
    {
      endpoint: 'POST /api/token/',
      form: 'components/forms/login-form.tsx',
      schema: { module: 'components/forms/login-form.schema.ts', export: 'loginSchema' },
      serializer: 'users.serializers.auth_serializers.LoginRequestSerializer',
      alsoPosts: [
        {
          field: 'anonymous_id',
          in: 'components/forms/login-form.actions.ts',
          why: "The browser's own identifier, read by the Server Action from the request's cookie rather than typed into the schema. A hidden input would be a value the page could rewrite; Django validates it as a UUID either way.",
        },
      ],
    },
    {
      endpoint: 'POST /api/register/',
      form: 'components/forms/signup-form.tsx',
      schema: { module: 'components/forms/signup-form.schema.ts', export: 'signupSchema' },
      serializer: 'users.serializers.auth_serializers.RegisterSerializer',
      alsoPosts: [
        {
          field: 'anonymous_id',
          in: 'components/forms/signup-form.actions.ts',
          why: 'Same value, same reason as login. This is the field whose absence once lost the signed-out cart on every signup.',
        },
      ],
    },
    {
      endpoint: 'POST /api/password/reset/',
      form: 'components/forms/forgot-password-form.tsx',
      schema: {
        module: 'components/forms/forgot-password-form.schema.ts',
        export: 'forgotPasswordSchema',
      },
      serializer: 'freetheplatform.auth.passwords.PasswordResetRequestSerializer',
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
