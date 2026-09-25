import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '../../lib/utils';
import { focusRingClassName } from '../../lib/controlState';

const badgeVariants = cva(
  cn(
    'inline-flex items-center justify-center rounded-md border px-2 py-0.5 text-label font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none aria-invalid:border-border-danger transition-[color,box-shadow] overflow-hidden',
    focusRingClassName,
  ),
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-action-primary text-text-on-brand [a&]:hover:bg-action-primary-hover',
        secondary:
          'border-transparent bg-surface-sunken text-text-primary [a&]:hover:bg-surface-sunken-strong',
        destructive:
          'border-transparent bg-fill-danger text-text-on-dark [a&]:hover:bg-fill-danger',
        outline: 'text-text-primary [a&]:hover:bg-surface-sunken [a&]:hover:text-text-primary',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
);

function Badge({
  className,
  variant,
  asChild = false,
  ...props
}: React.ComponentProps<'span'> & VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : 'span';

  return (
    <Comp data-slot="badge" className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
