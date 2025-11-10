import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Badge } from './ui/badge';
import '../css/CategoryCarousel.css';
import { useApiQuery } from '../hooks/useApiQuery';

// --- Type Definitions ---
type Category = {
  name: string;
  slug: string;
};

const CategoryBar: React.FC = () => {
  const navigate = useNavigate();
  const { data: categories = [], isLoading } = useApiQuery<Category[]>(
    ['primaryCategories'],
    '/categories/primary/',
    {},
    { refetchOnWindowFocus: false, staleTime: 1000 * 60 * 10 } // 10 minutes
  );

  const carouselRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const positionRef = useRef(0); // High-precision position
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    const scroll = () => {
      if (carouselRef.current) {
        const halfwayPoint = carouselRef.current.scrollWidth / 2;
        
        positionRef.current += 0.2;

        if (positionRef.current >= halfwayPoint) {
          positionRef.current = 0;
        }

        carouselRef.current.scrollLeft = positionRef.current;
      }
      animationFrameRef.current = requestAnimationFrame(scroll);
    };

    if (categories.length > 0 && !isHovering) {
      positionRef.current = carouselRef.current?.scrollLeft || 0;
      animationFrameRef.current = requestAnimationFrame(scroll);
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [categories, isHovering]);

  const handleRandomClick = () => {
    if (categories.length > 0) {
      const randomIndex = Math.floor(Math.random() * categories.length);
      const randomCategory = categories[randomIndex];
      navigate(`/search?primary_category_slug=${randomCategory.slug}`);
    }
  };

  if (isLoading || categories.length === 0) {
    return null;
  }

  const randomCategory: Category = { name: 'Random', slug: 'random-category-selection' };
  const categoriesWithRandom = [...categories, randomCategory];

  return (
    <div className="sticky top-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-40 border-b">
      <div 
        ref={carouselRef} 
        className="category-carousel overflow-x-auto pb-0"
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
      >
        <div className="flex items-center gap-4 py-1 px-2">
          {[...categoriesWithRandom, ...categoriesWithRandom].map((category, index) => (
            <div className="flex-shrink-0" key={`${category.slug}-${index}`}>
              {category.slug === 'random-category-selection' ? (
                <Badge 
                  variant="secondary" 
                  className="text-sm px-2 whitespace-nowrap bg-yellow-300 text-black italic hover:bg-yellow-400 cursor-pointer"
                  onClick={handleRandomClick}
                >
                  {category.name}
                </Badge>
              ) : (
                <Link to={`/search?primary_category_slug=${category.slug}`}>
                  <Badge variant="secondary" className="text-sm px-2 whitespace-nowrap hover:bg-transparent hover:text-foreground hover:border-foreground">
                    {category.name}
                  </Badge>
                </Link>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CategoryBar;