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
 * splitcart adds neither, and that is now a settled state rather than a gap.
 * The 125 findings this config reported when it arrived were all in
 * src/index.css, then unmodified `shadcn init` output with no semantic layer
 * for a local rule to protect. The token conversion in
 * _docs/convergence/tokens.md moved that vocabulary into src/styles/tokens.css
 * and `npm run lint:css` has been green since; it is part of `npm run check`.
 *
 * If a finding count ever comes back, the fix is in the stylesheet. Weakening
 * a rule here to make the count zero would hide the thing the rule is for.
 */
export default {
  ...stylelintBaseConfig,

  ignoreFiles: ['**/node_modules/**', '.next/**'],
};
