import * as React from 'react';

import { cn } from '../../lib/utils';
import { focusFieldClassName } from '../../lib/controlState';

function Input({ className, type, ...props }: React.ComponentProps<'input'>) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        'file:text-text-primary placeholder:text-text-muted selection:bg-action-primary selection:text-text-on-brand border-border-default h-9 w-full min-w-0 rounded-md border bg-transparent px-3 py-1 text-body shadow-xs transition-[color,box-shadow] file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-body-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
        focusFieldClassName,
        'aria-invalid:border-border-danger',
        className,
      )}
      {...props}
    />
  );
}

export { Input };
