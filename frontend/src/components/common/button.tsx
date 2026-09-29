/* Component registry: freetheplatform/frontend/registry/src/components/common/button.tsx
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { disabledUnavailableClassName, focusRingClassName } from '@/lib/controlState';
import { cn } from '@/lib/utils';

/** The compact, neutral application button (dashboard, dialogs, secondary controls). Not the customer-facing primary action, which is each site's marketing CTA. */
const buttonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-body font-medium transition-all [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 aria-invalid:border-border-danger",
    focusRingClassName,
    disabledUnavailableClassName,
  ],
  {
    variants: {
      variant: {
        default: 'bg-action-primary text-text-on-brand hover:bg-action-primary-hover',
        // `text-on-dark`, not `text-on-brand`: where the brand is light (splitcart's yellow) black on --fill-danger is 4.3:1, under AA.
        destructive: 'bg-fill-danger text-text-on-dark hover:bg-fill-danger/90',
        outline: 'border bg-surface-page shadow-xs hover:bg-surface-sunken hover:text-text-primary',
        secondary: 'bg-surface-tint text-text-primary hover:bg-surface-tint/80',
        ghost: 'hover:bg-surface-sunken hover:text-text-primary',
        // The link colour, the only accent rung that clears 4.5:1 on a light surface.
        link: 'text-link underline-offset-4 hover:underline hover:text-link-hover',
      },
      size: {
        default: 'h-9 px-4 py-2 has-[>svg]:px-3',
        sm: 'h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5',
        lg: 'h-10 rounded-md px-6 has-[>svg]:px-4',
        icon: 'size-9',
        'icon-sm': 'size-8',
        'icon-lg': 'size-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export type ButtonProps = React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

function Button({
  className,
  variant = 'default',
  size = 'default',
  asChild = false,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : 'button';

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
