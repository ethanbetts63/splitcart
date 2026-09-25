/**
 * Trailing-edge debounce.
 *
 * Split out of `lib/utils.ts` when that file became a component-registry copy,
 * which is `cn()` and nothing else — see `_docs/convergence/registry.md`.
 *
 * `CartContext` is the only caller: every quantity change updates the cart
 * optimistically and then schedules one sync, so holding a plus button does
 * not send a request per press.
 */
// `any` in the *constraint* only, and it is the one place it is load-bearing.
// A generic function type has to be constrained by something every function is
// assignable to. `unknown[]` does not work here: parameters are contravariant,
// so `(n: number) => void` is not assignable to `(...args: unknown[]) => void`,
// and every concrete caller would be rejected. The constraint is never a value
// type -- callers get `Parameters<F>`, fully typed -- so no `any` escapes into
// the signature this exposes.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function debounce<F extends (...args: any[]) => any>(
  func: F,
  wait: number,
): (...args: Parameters<F>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  return function executedFunction(...args: Parameters<F>): void {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout !== null) {
      clearTimeout(timeout);
    }

    timeout = setTimeout(later, wait);
  };
}
