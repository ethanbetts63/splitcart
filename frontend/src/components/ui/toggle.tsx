import * as React from 'react';
import * as TogglePrimitive from '@radix-ui/react-toggle';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '../../lib/utils';
import { focusRingClassName } from '../../lib/controlState';

const toggleVariants = cva(
  cn(
    "inline-flex items-center justify-center gap-2 rounded-md text-body font-medium hover:bg-surface-muted hover:text-text-muted disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-surface-sunken data-[state=on]:text-text-primary [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 [&_svg]:shrink-0 transition-[color,box-shadow] aria-invalid:border-border-danger whitespace-nowrap",
    focusRingClassName,
  ),
  {
    variants: {
      variant: {
        default: 'bg-transparent',
        outline:
          'border border-border-default bg-transparent shadow-xs hover:bg-surface-sunken hover:text-text-primary',
      },
      size: {
        default: 'h-9 px-2 min-w-9',
        sm: 'h-8 px-1.5 min-w-8',
        lg: 'h-10 px-2.5 min-w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

function Toggle({
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<typeof TogglePrimitive.Root> & VariantProps<typeof toggleVariants>) {
  return (
    <TogglePrimitive.Root
      data-slot="toggle"
      className={cn(toggleVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Toggle, toggleVariants };
