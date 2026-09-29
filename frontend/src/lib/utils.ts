/* Component registry: freetheplatform/frontend/registry/src/lib/utils.ts
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
import { clsx, type ClassValue } from 'clsx';
import { extendTailwindMerge } from 'tailwind-merge';

import { TEXT_SIZES } from './text-sizes.generated';

/**
 * tailwind-merge only knows stock sizes, so it would read `text-body-sm` as a colour and silently drop the real colour.
 * The names are generated from tokens.css's `@theme inline`; `npm run check:text-scale` fails when that file is stale.
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
