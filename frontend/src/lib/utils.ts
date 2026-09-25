import { clsx, type ClassValue } from 'clsx';
import { extendTailwindMerge } from 'tailwind-merge';

import { TEXT_SIZES } from './text-sizes.generated';

/**
 * tailwind-merge only knows Tailwind's stock sizes, so without this list it
 * misreads a custom name like `text-body-sm` as a *colour* and drops whatever
 * real colour it is merged with -- silently, at runtime, with no build error.
 * `cn()` existed here already and registered nothing, which is why a rung
 * utility and a stock size utility did not deduplicate.
 *
 * Names come straight out of tokens.css's `@theme inline` block via
 * `text-sizes.generated.ts`, so nothing here needs keeping in step by hand;
 * `npm run check:text-scale` fails when that file is stale.
 */
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      'font-size': [{ text: [...TEXT_SIZES] }],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const getCsrfToken = (): string | null => {
  let csrfToken: string | null = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, 'csrftoken'.length + 1) === 'csrftoken' + '=') {
        csrfToken = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
        break;
      }
    }
  }
  return csrfToken;
};

export const getAuthHeaders = (
  token: string | null,
  anonymousId: string | null = null,
): HeadersInit => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
  }

  if (token) {
    headers.Authorization = `Token ${token}`;
  }

  if (anonymousId) {
    headers['X-Anonymous-ID'] = anonymousId;
  }

  return headers;
};

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
