import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import '../css/CategoryCarousel.css';

// --- Type Definitions ---
type Category = {
  name: string;
  slug: string;
};

const CategoryBar: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const carouselRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const positionRef = useRef(0); // High-precision position
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    const fetchPopularCategories = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('/api/categories/popular/');
        if (!response.ok) {
          throw new Error('Failed to fetch popular categories');
        }
        const data: Category[] = await response.json();
        setCategories(data);
      } catch (error) {
        console.error(error);
        setCategories([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPopularCategories();
  }, []);

  useEffect(() => {
    const scroll = () => {
      if (carouselRef.current) {
        const halfwayPoint = carouselRef.current.scrollWidth / 2;
        
        // Increment our high-precision position
        positionRef.current += 0.2; // This is now the reliable speed control

        // Reset if we've scrolled past the first set of items
        if (positionRef.current >= halfwayPoint) {
          positionRef.current = 0;
        }

        // Apply the position to the actual scrollbar
        carouselRef.current.scrollLeft = positionRef.current;
      }
      animationFrameRef.current = requestAnimationFrame(scroll);
    };

    if (categories.length > 0 && !isHovering) {
      // When starting, sync our logical position with the actual scroll position
      positionRef.current = carouselRef.current?.scrollLeft || 0;
      animationFrameRef.current = requestAnimationFrame(scroll);
    }

    // Always return the cleanup function
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [categories, isHovering]);

  if (isLoading || categories.length === 0) {
    return null;
  }

  return (
    <div className="sticky top-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-40 border-b">
      <div 
        ref={carouselRef} 
        className="category-carousel overflow-x-auto pb-0"
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
      >
        <div className="flex items-center gap-4 py-1 px-2">
          {[...categories, ...categories].map((category, index) => (
            <div className="flex-shrink-0" key={`${category.slug}-${index}`}>
              <Link to={`/search?category_slug=${category.slug}`}>
                <Badge variant="secondary" className="text-sm px-2 whitespace-nowrap hover:bg-transparent hover:text-foreground hover:border-foreground">
                  {category.name}
                </Badge>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CategoryBar;
