interface AuthHeaders {
  'Content-Type': 'application/json';
  Authorization?: string;
  'X-Anonymous-ID'?: string;
}

export const getAuthHeaders = (token: string | null, anonymousId: string | null = null): AuthHeaders => {
  const headers: AuthHeaders = {
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
