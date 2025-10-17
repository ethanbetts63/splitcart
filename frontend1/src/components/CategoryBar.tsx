import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';

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
      <div className="container mx-auto px-4">
        <div className="flex items-center gap-4 overflow-x-auto py-3 scrollbar-hide">
          {categories.map((category) => (
            <Link to={`/search?category_slug=${category.slug}`} key={category.slug}>
              <Badge variant="outline" className="text-lg py-1 px-4 whitespace-nowrap">
                {category.name}
              </Badge>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CategoryBar;
