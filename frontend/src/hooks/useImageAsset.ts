import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';

const fetchImageAsBlob = async (src: string): Promise<Blob> => {
  const response = await fetch(src);
  if (!response.ok) {
    throw new Error(`Failed to fetch image: ${response.statusText}`);
  }
  return response.blob();
};

export const useImageAsset = (src: string) => {
  const { data: blob, isLoading, error } = useQuery<Blob, Error>(
    { 
      queryKey: ['imageAsset', src], 
      queryFn: () => fetchImageAsBlob(src), 
      staleTime: Infinity, // Keep image data fresh forever
      cacheTime: Infinity, // Keep image data in the cache forever
    }
  );

  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    if (blob) {
      const url = URL.createObjectURL(blob);
      setObjectUrl(url);

      // Clean up the object URL when the component unmounts or the blob changes
      return () => {
        URL.revokeObjectURL(url);
        setObjectUrl(null);
      };
    }
  }, [blob]);

  return { objectUrl, isLoading, error };
};