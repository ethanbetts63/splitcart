import { useQuery } from '@tanstack/react-query';

const fetchImageAndCreateUrl = async (src: string): Promise<string> => {
  const response = await fetch(src);
  if (!response.ok) {
    throw new Error(`Failed to fetch image: ${response.statusText}`);
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
};

export const useImageAsset = (src: string) => {
  const { data: objectUrl, isLoading, error } = useQuery<string, Error>(
    {
      queryKey: ['imageAsset', src],
      queryFn: () => fetchImageAndCreateUrl(src),
      staleTime: Infinity, // The fetched URL is static, so it never becomes stale.
      gcTime: Infinity,      // Keep the URL in the cache indefinitely.
    }
  );

  return { objectUrl, isLoading, error };
};