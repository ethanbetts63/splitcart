/* Component registry: freetheplatform/frontend/registry/src/components/common/badge.tsx
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { focusRingClassName } from '@/lib/controlState';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  [
    'inline-flex items-center justify-center rounded-full border px-2 py-0.5 text-label font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none aria-invalid:ring-fill-danger/20 aria-invalid:border-border-danger transition-[color,box-shadow] overflow-hidden',
    // For badges rendered as anchors (REG-7); inert on a <span>.
    focusRingClassName,
  ],
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-action-primary text-text-on-brand [a&]:hover:bg-action-primary-hover',
        secondary:
          'border-transparent bg-surface-tint text-text-primary [a&]:hover:bg-surface-tint/90',
        destructive:
          'border-transparent bg-fill-danger text-text-on-dark [a&]:hover:bg-fill-danger/90',
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
