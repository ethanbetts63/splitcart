/* Component registry: freetheplatform/frontend/registry/src/components/common/button.tsx
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { disabledUnavailableClassName, focusRingClassName } from '@/lib/controlState';
import { cn } from '@/lib/utils';

/**
 * The application button: compact, neutral, and the default everywhere inside
 * the dashboard, in dialogs, and for secondary controls on public pages.
 *
 * It is not the customer-facing primary action — that is each site's marketing
 * CTA (allbikes' `marketing/PrimaryCta`, freethedesk's `CtaButton`), which is
 * wide, uppercase and deliberately loud. Keep the boundary at intent rather
 * than at location: a public page may use both, but only one of them should be
 * the page's main action.
 */
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
        // `text-on-dark`, not `text-on-brand`: the danger fill is not the brand,
        // and the two tokens are the same white here only by coincidence. In a
        // repo whose brand is a light colour -- splitcart's yellow -- the brand
        // text role is black, and black on --fill-danger is 4.3:1, under AA.
        destructive: 'bg-fill-danger text-text-on-dark hover:bg-fill-danger/90',
        outline: 'border bg-surface-page shadow-xs hover:bg-surface-sunken hover:text-text-primary',
        secondary: 'bg-surface-tint text-text-primary hover:bg-surface-tint/80',
        ghost: 'hover:bg-surface-sunken hover:text-text-primary',
        // Was `text-primary`, which resolved to #000 -- the same colour as body
        // text. At rest this variant was indistinguishable from the words around
        // it, and only the hover underline ever said it was interactive. It is
        // now the link colour, which is also the only rung of the accent that
        // clears 4.5:1 on a light surface.
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

/**
 * No `forwardRef`: React 19 passes `ref` through as an ordinary prop, so the
 * wrapper was ceremony around a plain function -- and it was the only one left
 * in the three repositories.
 */
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
