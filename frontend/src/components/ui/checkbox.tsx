import * as React from 'react';
import * as CheckboxPrimitive from '@radix-ui/react-checkbox';
import { CheckIcon } from 'lucide-react';

import { cn } from '../../lib/utils';
import { focusRingClassName } from '../../lib/controlState';

function Checkbox({ className, ...props }: React.ComponentProps<typeof CheckboxPrimitive.Root>) {
  return (
    <CheckboxPrimitive.Root
      data-slot="checkbox"
      className={cn(
        'peer border-border-default data-[state=checked]:bg-action-primary data-[state=checked]:text-text-on-brand data-[state=checked]:border-action-primary aria-invalid:border-border-danger size-4 shrink-0 rounded-xs border shadow-xs transition-shadow disabled:cursor-not-allowed disabled:opacity-50',
        focusRingClassName,
        className,
      )}
      {...props}
    >
      <CheckboxPrimitive.Indicator
        data-slot="checkbox-indicator"
        className="grid place-content-center text-current transition-none"
      >
        <CheckIcon className="size-3.5" />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
}

export { Checkbox };
