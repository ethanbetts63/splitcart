/* Component registry: freetheplatform/frontend/registry/src/components/common/input.tsx
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
import * as React from 'react';

import { disabledUnavailableClassName, focusFieldClassName } from '@/lib/controlState';
import { cn } from '@/lib/utils';

/* The 1rem floor is an iOS Safari threshold: a focused control under 16px zooms the viewport and never zooms back.
   `--text-body` is ~14px at phone widths. A property, not a `text-*` utility, so Tailwind Merge cannot read it as a colour. */
function Input({ className, type, ...props }: React.ComponentProps<'input'>) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        'file:text-text-primary placeholder:text-text-muted selection:bg-action-primary selection:text-text-on-brand border-border-strong h-9 w-full min-w-0 rounded-md border bg-transparent px-3 py-1 [font-size:max(1rem,var(--text-body))] shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-body file:font-medium',
        focusFieldClassName,
        'aria-invalid:ring-fill-danger/20 aria-invalid:border-border-danger',
        disabledUnavailableClassName,
        className,
      )}
      {...props}
    />
  );
}

export { Input };
