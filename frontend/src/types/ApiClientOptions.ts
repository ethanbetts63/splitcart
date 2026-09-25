import type { JsonBody } from './JsonBody';

export interface ApiClientOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: JsonBody | FormData;
  signal?: AbortSignal;
}
