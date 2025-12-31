import { type ApiClient } from './apiClient';

interface FaqItem {
  question: string;
  answer: string;
}

export const fetchFaqsAPI = (apiClient: ApiClient, page: string): Promise<FaqItem[]> => {
  return apiClient.get<FaqItem[]>(`/api/faqs/?page=${page}`);
};
