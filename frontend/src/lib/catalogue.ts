import { SERVER_API_BASE_URL } from './serverApi';

/**
 * A public catalogue read for a server-rendered page, cached for `revalidate`
 * seconds.
 *
 * `null` means Django answered that there is no such record. Anything else
 * that goes wrong -- Django unreachable, or answering 5xx -- throws, and that
 * is the point. These pages used to catch every failure and render empty, so a
 * production build against a dead API succeeded and prerendered pages that
 * looked exactly like good ones with nothing in them. Thrown instead, the
 * build fails and says why, and an ISR revalidation that fails keeps serving
 * the last good page rather than replacing it with an empty one.
 */
export async function fetchCatalogue<T>(path: string, revalidate: number): Promise<T | null> {
  const url = `${SERVER_API_BASE_URL}${path}`;
  let response: Response;
  try {
    response = await fetch(url, { next: { revalidate } });
  } catch (cause) {
    throw new Error(`Django API unreachable at ${url}`, { cause });
  }
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new Error(`Django API answered ${response.status} for ${url}`);
  }
  return (await response.json()) as T;
}
