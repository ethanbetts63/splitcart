import { cookies } from 'next/headers';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * The signed-out cart's identifier, for a Server Action to hand to a door.
 *
 * Read from the request's own cookie rather than posted from the page, so no
 * hidden input carries it. Only a UUID is passed on: an older browser without
 * `crypto.randomUUID` minted something else, and Django validates the field as
 * a UUID -- sending that would refuse the sign-in over a cart that cannot exist.
 */
export async function anonymousIdFromCookies(): Promise<string | null> {
  const value = (await cookies()).get('anonymousId')?.value;
  return value && UUID.test(value) ? value : null;
}
