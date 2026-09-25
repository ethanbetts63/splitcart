import * as React from 'react';

const MOBILE_BREAKPOINT = 768;
const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`;

const subscribe = (onStoreChange: () => void) => {
  const mql = window.matchMedia(MOBILE_QUERY);
  mql.addEventListener('change', onStoreChange);
  return () => mql.removeEventListener('change', onStoreChange);
};

/**
 * Whether the viewport is narrower than the sidebar's mobile breakpoint.
 *
 * matchMedia is an external store, so this reads it with the hook React
 * provides for one instead of mirroring it into state from an effect. The
 * server snapshot is `false`: there is no viewport on the server, and
 * answering "not mobile" keeps the server and client HTML identical.
 */
export function useIsMobile() {
  return React.useSyncExternalStore(
    subscribe,
    () => window.matchMedia(MOBILE_QUERY).matches,
    () => false,
  );
}
