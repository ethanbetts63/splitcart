import { stylelintBaseConfig } from '../../freetheplatform/frontend/lint/stylelint-base.mjs';

/**
 * CSS is the half of this codebase ESLint cannot see.
 *
 * The rule set is imported, never copied: the canonical source is
 * freetheplatform/frontend/lint/stylelint-base.mjs, which allbikes and
 * freethedesk read too, so the three sites cannot drift into disagreeing
 * about what a token is for (LINT-10). What a site adds locally is its own
 * `ignoreFiles` and any rule that guards its own foundation.
 *
 * splitcart adds neither yet, and that is the honest state rather than an
 * oversight. src/index.css is still unmodified `shadcn init` output: a
 * palette with no semantic layer on top of it, so there is no vocabulary for
 * a local rule to protect. `npm run lint:css` is red today for exactly that
 * reason, and the findings are the work in
 * _docs/convergence/tokens.md -- they belong to that plan, not to this
 * config. Weakening a rule here to make the count zero would hide the thing
 * the plan exists to fix.
 */
export default {
  ...stylelintBaseConfig,

  ignoreFiles: ['**/node_modules/**', '.next/**'],
};
