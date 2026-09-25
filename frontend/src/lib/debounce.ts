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
