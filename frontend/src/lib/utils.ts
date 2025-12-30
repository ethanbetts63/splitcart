import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const getCsrfToken = (): string | null => {
  let csrfToken: string | null = null;
  if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
              csrfToken = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
              break;
          }
      }
  }
  return csrfToken;
};

export const getAuthHeaders = (token: string | null, anonymousId: string | null = null): HeadersInit => {
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
