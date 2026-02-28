import { useState, useEffect, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import type { PrimaryCategory } from '../types/PrimaryCategory';

// --- Configuration ---
const PRIORITY_CATEGORIES = ['deals', 'sweets', 'meat'];

export const useCarouselManager = (numSlots: number) => {
  const { data: allCategories } = useApiQuery<PrimaryCategory[]>(
    ['primary-categories'],
    '/api/categories/primary/',
    {},
    {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 60, // 1 hour
    }
  );

  const [candidateQueue, setCandidateQueue] = useState<PrimaryCategory[]>([]);
  const [carouselSlots, setCarouselSlots] = useState<(PrimaryCategory | null)[]>(Array(numSlots).fill(null));

  // --- Step 1: Build the initial candidate list and populate slots ---
  useEffect(() => {
    if (allCategories && allCategories.length > 0) {
      const priority = PRIORITY_CATEGORIES.map(slug => 
        allCategories.find(cat => cat.slug === slug)
      ).filter((cat): cat is PrimaryCategory => !!cat);

      const remaining = allCategories.filter(cat => 
        !PRIORITY_CATEGORIES.includes(cat.slug)
      );

      // Shuffle the remaining categories
      for (let i = remaining.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [remaining[i], remaining[j]] = [remaining[j], remaining[i]];
      }

      const initialCandidates = [...priority, ...remaining];
      
      setCarouselSlots(initialCandidates.slice(0, numSlots));
      setCandidateQueue(initialCandidates.slice(numSlots));
    }
  }, [allCategories, numSlots]);

  // --- Step 2: Handle validation and replacement ---
  const handleValidation = useCallback((isValid: boolean, slotIndex: number) => {
    if (!isValid) {
      setCarouselSlots(currentSlots => {
        const newSlots = [...currentSlots];
        const newQueue = [...candidateQueue];
        const nextCandidate = newQueue.shift();
        
        // Replace the invalid item at the specific index with the next candidate or null
        newSlots[slotIndex] = nextCandidate || null;
        
        setCandidateQueue(newQueue);
        return newSlots;
      });
    }
  }, [candidateQueue]);

  return { carouselSlots, handleValidation };
};
