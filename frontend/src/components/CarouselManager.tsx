import React, { useState, useEffect, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import { ProductCarousel } from './ProductCarousel';

// Type for the primary category data fetched from the API
type PrimaryCategory = {
  name: string;
  slug: string;
};

// --- Configuration ---
const PRIORITY_CATEGORIES = ['deals', 'sweets', 'meat'];
const NUM_CAROUSELS_TO_DISPLAY = 6;

const CarouselManager: React.FC<{ storeIds?: number[] }> = ({ storeIds }) => {
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
  const [displayedCarousels, setDisplayedCarousels] = useState<PrimaryCategory[]>([]);

  // --- Step 1: Build the initial candidate list ---
  useEffect(() => {
    if (allCategories) {
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
      
      setDisplayedCarousels(initialCandidates.slice(0, NUM_CAROUSELS_TO_DISPLAY));
      setCandidateQueue(initialCandidates.slice(NUM_CAROUSELS_TO_DISPLAY));
    }
  }, [allCategories]);

  // --- Step 2: Handle validation and replacement ---
  const handleValidation = useCallback((slug: string, isValid: boolean) => {
    if (!isValid) {
      console.log(`Carousel for '${slug}' is invalid. Attempting to replace.`);
      setDisplayedCarousels(currentCarousels => {
        const newQueue = [...candidateQueue];
        const nextCandidate = newQueue.shift();

        if (!nextCandidate) {
          // No more candidates, just remove the invalid one
          return currentCarousels.filter(c => c.slug !== slug);
        }

        // Replace the invalid carousel with the next candidate
        const newCarousels = currentCarousels.map(c => 
          c.slug === slug ? nextCandidate : c
        );
        
        setCandidateQueue(newQueue);
        return newCarousels;
      });
    }
  }, [candidateQueue]);

  if (!storeIds || storeIds.length === 0) {
    // Or some placeholder/message
    return null;
  }

  return (
    <div className="space-y-8">
      {displayedCarousels.map(category => (
        <ProductCarousel
          key={category.slug} // Use slug as key for stable identity
          title={category.name}
          sourceUrl="/api/products/"
          storeIds={storeIds}
          primaryCategorySlug={category.slug}
          onValidation={handleValidation}
        />
      ))}
    </div>
  );
};

export default CarouselManager;
