import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTypeScript from 'eslint-config-next/typescript';
import { cssModuleBoundaryImports } from '../../freetheplatform/frontend/lint/design-system-eslint.mjs';

export default defineConfig([
  ...nextVitals,
  ...nextTypeScript,
  {
    // CSS Modules are an approved-exception boundary, not a default - see
    // lint-rules.md's "Allowed handwritten CSS" table. splitcart has no CSS
    // module today and src/index.css is its one stylesheet, so this rule costs
    // nothing right now; it is here so that the first one to appear has to be
    // argued for in this file rather than arriving as a quiet import.
    //
    // The rule definition is imported, never copied (LINT-10): the canonical
    // source is freetheplatform/frontend/lint/design-system-eslint.mjs, which
    // allbikes and freethedesk read too.
    name: 'splitcart/css-module-boundary',
    files: ['src/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': cssModuleBoundaryImports(),
    },
  },
  {
    // `next/image` is not this site's image strategy, and that is a decision
    // rather than an omission. next.config.ts sets
    // `images.disableStaticImages: true`; every photographic asset in
    // src/assets ships as a pre-generated webp ladder (-320w, -640w, -768w,
    // -1024w, -1280w) built at author time; and src/lib/assets.ts turns that
    // ladder into `src`/`srcSet`/`sizes` at the call site. That is the same
    // job next/image does, done ahead of time and without a runtime optimiser
    // in front of it, so the rule's advice here is to replace a working
    // implementation with a second one.
    //
    // Scoped to the one rule, with the reason recorded, per LINT-9 -- not a
    // file-glob ignore. If the ladder ever goes away, so should this.
    name: 'splitcart/hand-rolled-responsive-images',
    files: ['src/**/*.{ts,tsx}'],
    rules: {
      '@next/next/no-img-element': 'off',
    },
  },
  // NOT YET HERE: the design-system block the other three repos run,
  //
  //   rules: { 'no-restricted-syntax': designSystemNoRestrictedSyntax() }
  //
  // from the same shared module. It is the ESLint half of the token rules, and
  // splitcart's markup is still unmodified shadcn - raw palette rungs
  // (bg-white, text-gray-500) and raw type sizes (text-2xl) throughout - so
  // turning it on today reports several hundred findings that are all one
  // piece of work. That work is _docs/convergence/tokens.md, and this block
  // arrives with it. Adding it here first would only mean a permanently red
  // `npm run lint`, which is a lint nobody reads (LINT-9).
  //
  // When it lands: one config object, one rule key, one array. ESLint flat
  // config REPLACES a rule's options rather than merging them, so splitting
  // the design-system rules across several blocks silently disables all but
  // the last - allbikes learned that expensively.
  globalIgnores(['.next/**', 'out/**', 'build/**', 'node_modules/**', 'next-env.d.ts']),
]);
