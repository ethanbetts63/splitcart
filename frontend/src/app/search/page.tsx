import { Suspense } from 'react';

import LoadingSpinner from '@/components/LoadingSpinner';
import SearchResultsPage from '@/page_components/SearchResultsPage';

/**
 * Search is state 4 — robots-disallowed — and nothing else.
 *
 * Every distinct `?q=` is a new URL, so this is an unbounded query surface and
 * the right instrument is the disallow, declared once in
 * `app/robots.txt/route.ts`. The `noindex` this page used to export alongside
 * it was inert: a disallowed page is never fetched, so the directive on it is
 * never read. seo-standard.md section 2 forbids declaring both states.
 */

export const dynamic = 'force-dynamic';

export default function Page() {
  // useSearchParams() needs a boundary of its own now that the shell has none.
  return (
    <Suspense fallback={<LoadingSpinner fullScreen />}>
      <SearchResultsPage />
    </Suspense>
  );
}
