import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTypeScript from 'eslint-config-next/typescript';
import {
  cssModuleBoundaryImports,
  designSystemNoRestrictedSyntax,
} from '../../freetheplatform/frontend/lint/design-system-eslint.mjs';

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
  {
    // The design-system rules the other three repos run: raw palette rungs,
    // raw Tailwind type sizes, retired rungs, status hues, the rail, dynamic
    // class fragments and arbitrary scale values. Imported from the same
    // shared module rather than restated (LINT-10).
    //
    // ONE config object, ONE rule key, ONE array. ESLint flat config REPLACES
    // a rule's options rather than merging them across matching objects, so
    // splitting these across several blocks silently disables all but the
    // last - allbikes learned that expensively. Anything that needs adding
    // goes into this array, never into a second `no-restricted-syntax`.
    name: 'splitcart/design-system',
    files: ['src/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-syntax': designSystemNoRestrictedSyntax(),
    },
  },
  globalIgnores(['.next/**', 'out/**', 'build/**', 'node_modules/**', 'next-env.d.ts']),
]);
