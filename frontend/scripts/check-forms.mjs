#!/usr/bin/env node
/**
 * Thin entry point. The engines are shared — edit them in
 * `freetheplatform/frontend/registry/tooling/forms/` and re-sync, never here.
 * `form-ledger.mjs` and `walk.mjs` are byte-identical copies; `form-hygiene.mjs`
 * is adapted, and says at the top exactly how and why.
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
    // Track B — useActionState over an action that validates the schema beside
    // the form. A *client* action, not a Server Action: splitcart holds a DRF
    // token in `localStorage` and attaches it from the browser, so there is no
    // session for a Next server to forward. Each form says so at its top.
    { file: 'components/ui/login-form.tsx', track: 'B' },
    { file: 'components/ui/signup-form.tsx', track: 'B' },
    { file: 'page_components/dialog-pages/CartPage.tsx', track: 'B' },
  ],
});

checkFormHygiene({
  root,
  // No `sessionCookies`, and that is the fact rather than an omission: there is
  // no `lib/serverApi.ts`, no Server Action and no session cookie pair to
  // forward, so FORMS-10 and FORMS-11 have no subject here. They are recorded
  // `n/a` with that reason in the conformance ledger, and become live when
  // `_docs/convergence/auth-migration.md` issues `splitcart_access` /
  // `splitcart_refresh`. See the note at the top of `forms/form-hygiene.mjs`.
  envReaders: [
    {
      file: 'app/bargains/page.tsx',
      why: 'Reads DJANGO_API_URL inline for its server-side fetch. FORMS-9 wants one owner; that owner is lib/serverApi.ts, which cannot exist until auth-migration.md gives this app a server-side session. Listed rather than hidden so the consolidation has a list to work from.',
    },
    {
      file: 'app/categories/[slug]/page.tsx',
      why: 'Same inline read, same owner-in-waiting. See app/bargains/page.tsx.',
    },
    {
      file: 'app/page.tsx',
      why: 'Same inline read, same owner-in-waiting. See app/bargains/page.tsx.',
    },
    {
      file: 'app/product/[slug]/page.tsx',
      why: 'Same inline read, same owner-in-waiting. See app/bargains/page.tsx.',
    },
  ],
});
