import type { CartSubstitution } from './CartSubstitution';

export type OnQuantityChangeCallback = (sub: CartSubstitution, quantity: number) => Promise<void>;
