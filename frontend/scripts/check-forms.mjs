#!/usr/bin/env node
/**
 * Thin entry point. The engines are shared — edit them in
 * `freetheplatform/frontend/registry/tooling/forms/` and re-sync, never here.
 *
 * The ledger below is the repo-specific part and is the whole point: a new form
 * cannot be added without a row saying which track it is on, and a row saying
 * `excluded` cannot be added without a reason. See
 * `../../../freetheplatform/_docs/forms-standard.md` for the tracks and
 * `../../_docs/convergence/forms.md` for what is still outstanding.
 *
 * ## What is not in the ledger, and why that is not an omission
 *
 * FORMS-1 runs both ways: every file rendering a `<form>` has a row, and every
 * row points at a file that renders one. So the two candidates the survey
 * looked hardest at get their reasons here rather than as rows the engine would
 * reject for pointing at nothing:
 *
 *   - `components/NavSearchBar.tsx` — a search field that calls `router.push`.
 *     No network write, no validation burden, and no `<form>` element.
 *   - `components/settings-dialog.tsx` — a Cart/Home/Close switcher. It renders
 *     controls and submits nothing.
 *
 * `page_components/ContactPage.tsx` gets no mention in either place: despite
 * the name it is static marketing copy with an email address in prose. There
 * is no contact form in this application.
 */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkFormLedger } from './forms/form-ledger.mjs';
import { checkFormHygiene } from './forms/form-hygiene.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

checkFormLedger({
  root,
  ledger: [
    // Track B — useActionState over a Server Action that validates the schema
    // beside the form and calls Django once through `lib/serverApi.ts`.
    { file: 'components/forms/login-form.tsx', track: 'B' },
    { file: 'components/forms/signup-form.tsx', track: 'B' },
    { file: 'components/forms/forgot-password-form.tsx', track: 'B' },
    { file: 'components/forms/reset-password-form.tsx', track: 'B' },
    // Track B with a client action: the rename goes through `CartContext`,
    // which owns the cart's state and updates it from the answer.
    { file: 'page_components/dialog-pages/CartPage.tsx', track: 'B' },
  ],
});

checkFormHygiene({
  root,
  sessionCookies: ['splitcart_access', 'splitcart_refresh'],
  envReaders: [
    {
      file: 'lib/serverApi.ts',
      why: 'Owns SERVER_API_BASE_URL and the 127.0.0.1 fallback.',
    },
  ],
});
