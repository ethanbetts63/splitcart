import type { CartSubstitution } from './CartSubstitution';

export type OnApproveCallback = (sub: CartSubstitution) => Promise<void>;
