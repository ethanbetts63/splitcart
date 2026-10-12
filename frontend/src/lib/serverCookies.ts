/* Component registry: freetheplatform/frontend/registry/src/lib/serverCookies.ts
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
import { cookies } from 'next/headers';

interface ParsedCookie {
  name: string;
  value: string;
  options: {
    maxAge?: number;
    httpOnly?: boolean;
    secure?: boolean;
    sameSite?: 'strict' | 'lax' | 'none';
    path?: string;
  };
}

function parseSetCookie(header: string): ParsedCookie | null {
  const [pair, ...attributes] = header.split(';').map((part) => part.trim());
  const separator = pair.indexOf('=');
  if (separator === -1) return null;

  const options: ParsedCookie['options'] = {};
  for (const attribute of attributes) {
    const [rawKey, rawValue] = attribute.split('=');
    switch (rawKey.trim().toLowerCase()) {
      case 'max-age':
        options.maxAge = Number(rawValue);
        break;
      case 'path':
        options.path = rawValue;
        break;
      case 'httponly':
        options.httpOnly = true;
        break;
      case 'secure':
        options.secure = true;
        break;
      case 'samesite':
        options.sameSite = rawValue?.trim().toLowerCase() as 'strict' | 'lax' | 'none';
        break;
    }
  }

  return { name: pair.slice(0, separator), value: pair.slice(separator + 1), options };
}

/** Copies every upstream Django `Set-Cookie` header, with its attributes, onto this request's cookie jar: what a browser does for a same-origin `credentials: 'include'` fetch. */
export async function relaySetCookies(response: Response): Promise<void> {
  const setCookieHeaders = response.headers.getSetCookie();
  if (setCookieHeaders.length === 0) return;

  const cookieStore = await cookies();
  for (const header of setCookieHeaders) {
    const parsed = parseSetCookie(header);
    if (parsed) cookieStore.set(parsed.name, parsed.value, parsed.options);
  }
}
