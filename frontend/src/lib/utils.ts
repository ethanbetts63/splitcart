import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const getAuthHeaders = (token: string | null, anonymousId: string | null = null): HeadersInit => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Token ${token}`;
  }

  if (anonymousId) {
    headers['X-Anonymous-ID'] = anonymousId;
  }

  return headers;
};
