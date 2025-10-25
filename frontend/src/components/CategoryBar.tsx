import React, { useState, useEffect } from 'react';
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
        // In case of an error, we just won't show the bar.
        setCategories([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPopularCategories();
  }, []);

  if (isLoading || categories.length === 0) {
    return null; // Don't render anything while loading or if there are no categories
  }

  return (
    <div className="sticky top-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-40 border-b">
      <div className="category-carousel overflow-x-auto pb-0">
        <div className="flex items-center gap-4 py-1 px-2">
          {categories.map((category) => (
            <div className="flex-shrink-0" key={category.slug}>
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
