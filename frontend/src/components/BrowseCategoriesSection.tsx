import { Link } from 'react-router-dom';

import bargainsIcon from '../assets/food_svgs/Tools-Kitchen-Scale--Streamline-Ultimate.svg';
import snacksIcon from '../assets/food_svgs/Ice-Cream-Cone--Streamline-Ultimate.svg';
import meatIcon from '../assets/food_svgs/Seafood-Squid--Streamline-Ultimate.svg';
import dairyIcon from '../assets/food_svgs/Animal-Products-Egg--Streamline-Ultimate.svg';
import fruitVegIcon from '../assets/food_svgs/Fruit-Watermelon--Streamline-Ultimate.svg';
import pantryIcon from '../assets/food_svgs/Pasta-Bowl-Warm--Streamline-Ultimate.svg';
import healthIcon from '../assets/food_svgs/Water-Bottle-Glass--Streamline-Ultimate.svg';

const categories = [
  {
    title: 'Bargains',
    description: 'The biggest discounts across all stores/categories right now.',
    href: '/bargains',
    icon: bargainsIcon,
    featured: true,
  },
  {
    title: 'Snacks & Sweets',
    description: 'Chips, chocolate, biscuits and more.',
    href: '/categories/snacks-and-sweets',
    icon: snacksIcon,
  },
  {
    title: 'Meat & Seafood',
    description: 'Fresh cuts and seafood from every store.',
    href: '/categories/meat-and-seafood',
    icon: meatIcon,
  },
  {
    title: 'Dairy',
    description: 'Milk, cheese, yoghurt and eggs.',
    href: '/categories/dairy',
    icon: dairyIcon,
  },
  {
    title: 'Fruit, Veg & Spices',
    description: 'Fresh produce at the best price.',
    href: '/categories/fruit-veg-and-spices',
    icon: fruitVegIcon,
  },
  {
    title: 'Pantry & International',
    description: 'Staples, sauces and world foods.',
    href: '/categories/pantry-and-international',
    icon: pantryIcon,
  },
  {
    title: 'Health, Beauty & Supplements',
    description: 'Vitamins, skincare and personal care.',
    href: '/categories/health-beauty-and-supplements',
    icon: healthIcon,
  },
];

export const BrowseCategoriesSection = () => {
  return (
    <div className="container mx-auto px-4 py-10">
      <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-6 text-center">
        Browse Bargains by Category
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {categories.map((cat) => (
          <Link
            key={cat.href}
            to={cat.href}
            className={`group flex flex-col items-center text-center rounded-xl p-5 shadow-sm border transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 ${
              cat.featured
                ? 'bg-yellow-300 border-yellow-400 hover:bg-yellow-200'
                : 'bg-white border-gray-200 hover:border-yellow-300'
            }`}
          >
            <img
              src={cat.icon}
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
