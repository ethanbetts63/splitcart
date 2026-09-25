/* Component registry: freetheplatform/frontend/registry/src/lib/utils.ts
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
import { clsx, type ClassValue } from 'clsx';
import { extendTailwindMerge } from 'tailwind-merge';

import { TEXT_SIZES } from './text-sizes.generated';

/**
 * tailwind-merge only knows Tailwind's stock sizes, so without this list it
 * misreads a custom name like `text-body-sm` as a *colour* and drops whatever
 * real colour it is merged with — silently, at runtime, with no build error.
 * This is how allbikes' `PrimaryCta size="large"` once rendered black text on
 * its green background.
 *
 * Names come straight out of tokens.css's `@theme inline` block via
 * `text-sizes.generated.ts`, so nothing here needs keeping in step by hand;
 * `npm run check:text-scale` fails when that file is stale.
 */
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      'font-size': [{ text: [...TEXT_SIZES] }],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
