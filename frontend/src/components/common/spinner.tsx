/* Component registry: freetheplatform/frontend/registry/src/components/common/spinner.tsx
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
import { Loader2Icon } from 'lucide-react';

import { cn } from '@/lib/utils';

function Spinner({ className, ...props }: React.ComponentProps<'svg'>) {
  return (
    <Loader2Icon
      role="status"
      aria-label="Loading"
      className={cn('size-4 animate-spin text-text-primary', className)}
      {...props}
    />
  );
}

export { Spinner };
