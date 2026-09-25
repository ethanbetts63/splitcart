/* Component registry: freetheplatform/frontend/registry/src/components/common/input.tsx
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
import * as React from 'react';

import { disabledUnavailableClassName, focusFieldClassName } from '@/lib/controlState';
import { cn } from '@/lib/utils';

/* The 1rem floor is an iOS Safari threshold rather than a type decision: a
   focused control whose text is under 16px zooms the viewport in and never
   zooms back out, stranding the rest of the form off-screen. `--text-body` is
   fluid and resolves to ~14px at phone widths, so every field in all three
   repos tripped it. Written as a property rather than a `text-*` utility so it
   cannot be read as a colour by Tailwind Merge, and it is a no-op at >=1240px
   where the rung is already 1rem. */
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
