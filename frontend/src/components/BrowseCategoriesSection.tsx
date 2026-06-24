import Link from 'next/link';
import { assetSrc } from '@/lib/assets';
import { CATEGORIES } from '@/data/categories';

export const BrowseCategoriesSection = () => {
  return (
    <div className="container mx-auto px-4 py-10">
      <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-6 text-center">
        Browse Bargains by Category
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {CATEGORIES.map((cat) => (
          <Link
            key={cat.href}
            href={cat.href}
            className={`group flex flex-col items-center text-center rounded-xl p-5 shadow-sm border transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 ${
              cat.featured
                ? 'bg-yellow-300 border-yellow-400 hover:bg-yellow-200'
                : 'bg-white border-gray-200 hover:border-yellow-300'
            }`}
          >
            <img
              src={assetSrc(cat.icon)}
              alt=""
              aria-hidden="true"
              className="w-14 h-14 mb-3"
            />
            <h3 className="font-bold text-gray-900 text-sm md:text-base leading-tight">
              {cat.title}
            </h3>
            <p className="text-xs text-gray-600 mt-1 leading-snug hidden sm:block">
              {cat.description}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
};
