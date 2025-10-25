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
  const animationFrameRef = useRef<number>();
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

  const startScrolling = useCallback(() => {
    if (!carouselRef.current || isHovering) return;

    const scroll = () => {
      if (carouselRef.current) {
        const { scrollLeft, scrollWidth } = carouselRef.current;
        // The halfway point is the end of the original content
        const halfwayPoint = scrollWidth / 2;

        if (scrollLeft >= halfwayPoint) {
          carouselRef.current.scrollLeft = 0; // Jump back to the start
        } else {
          carouselRef.current.scrollLeft += 0.5; // Adjust for speed
        }
      }
      animationFrameRef.current = requestAnimationFrame(scroll);
    };

    animationFrameRef.current = requestAnimationFrame(scroll);
  }, [isHovering]);

  useEffect(() => {
    // Only start scrolling if we have categories and the user is not hovering
    if (categories.length > 0 && !isHovering) {
      startScrolling();
    }

    // Cleanup function to cancel the animation frame when the component unmounts or dependencies change
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [categories, isHovering, startScrolling]);

  if (isLoading || categories.length === 0) {
    return null; // Don't render anything while loading or if there are no categories
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
          {/* Render the list of categories twice for the infinite loop effect */}
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
