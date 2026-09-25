import { useCallback, useSyncExternalStore } from 'react';

/**
 * Track a CSS media query.
 *
 * `useSyncExternalStore` rather than state-plus-effect: matchMedia is an
 * external store, and reading it through the hook React provides for that
 * removes the extra render the old effect caused on every mount. The server
 * snapshot is `false` because there is no viewport to measure there, which
 * keeps the server and client HTML identical and leaves the real answer to
 * the first client read.
 */
function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (onStoreChange: () => void) => {
      const media = window.matchMedia(query);
      media.addEventListener('change', onStoreChange);
      return () => media.removeEventListener('change', onStoreChange);
    },
    [query],
  );

  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(query).matches,
    () => false,
  );
}

export default useMediaQuery;
