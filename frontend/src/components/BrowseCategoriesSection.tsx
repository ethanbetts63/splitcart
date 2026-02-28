import { Link } from 'react-router-dom';

import bargainsIcon from '../assets/food_svgs/Tools-Kitchen-Scale--Streamline-Ultimate.svg';
import snacksIcon from '../assets/food_svgs/Fast-Food-French-Fries--Streamline-Ultimate.svg';
import sweetsIcon from '../assets/food_svgs/Ice-Cream-Cone--Streamline-Ultimate.svg';
import meatIcon from '../assets/food_svgs/Barbecue-Grill--Streamline-Ultimate.svg';
import dairyIcon from '../assets/food_svgs/Animal-Products-Egg--Streamline-Ultimate.svg';
import fruitVegIcon from '../assets/food_svgs/Fruit-Watermelon--Streamline-Ultimate.svg';
import spiceIcon from '../assets/food_svgs/Seasoning-Food--Streamline-Ultimate.svg';
import pantryIcon from '../assets/food_svgs/Pasta-Bowl-Warm--Streamline-Ultimate.svg';
import internationalIcon from '../assets/food_svgs/Seafood-Sushi--Streamline-Ultimate.svg';
import bakeryIcon from '../assets/food_svgs/Bread-Loaf--Streamline-Ultimate.svg';
import drinksIcon from '../assets/food_svgs/Soft-Drinks-Bottle-1--Streamline-Ultimate.svg';
import healthIcon from '../assets/food_svgs/Water-Bottle-Glass--Streamline-Ultimate.svg';
import homeIcon from '../assets/food_svgs/Kitchenware-Spatula-1--Streamline-Ultimate.svg';
import babyIcon from '../assets/food_svgs/Coffee-Cold--Streamline-Ultimate.svg';
import petIcon from '../assets/food_svgs/Beer-Opener-1--Streamline-Ultimate.svg';

const categories = [
  {
    title: 'Bargains',
    description: 'The biggest discounts across all stores.',
    href: '/bargains',
    icon: bargainsIcon,
    featured: true,
  },
  {
    title: 'Snacks',
    description: 'Chips, crackers, and savoury treats.',
    href: '/categories/snacks',
    icon: snacksIcon,
  },
  {
    title: 'Sweets & Chocolate',
    description: 'Chocolate, lollies, and desserts.',
    href: '/categories/sweets',
    icon: sweetsIcon,
  },
  {
    title: 'Meat & Seafood',
    description: 'Fresh cuts, poultry, and seafood.',
    href: '/categories/meat-and-seafood',
    icon: meatIcon,
  },
  {
    title: 'Dairy & Eggs',
    description: 'Milk, cheese, eggs, and yoghurt.',
    href: '/categories/dairy-and-eggs',
    icon: dairyIcon,
  },
  {
    title: 'Fruit & Veg',
    description: 'Fresh produce from every store.',
    href: '/categories/fruit-and-veg',
    icon: fruitVegIcon,
  },
  {
    title: 'Herbs & Spices',
    description: 'Dried herbs, spices, and seasonings.',
    href: '/categories/spices',
    icon: spiceIcon,
  },
  {
    title: 'Pantry',
    description: 'Staples, sauces, and canned goods.',
    href: '/categories/pantry',
    icon: pantryIcon,
  },
  {
    title: 'International Foods',
    description: 'Asian, Indian, and global ingredients.',
    href: '/categories/international',
    icon: internationalIcon,
  },
  {
    title: 'Bakery & Deli',
    description: 'Bread, pastries, and cured meats.',
    href: '/categories/bakery-and-deli',
    icon: bakeryIcon,
  },
  {
    title: 'Drinks',
    description: 'Soft drinks, juices, and water.',
    href: '/categories/drinks',
    icon: drinksIcon,
  },
  {
    title: 'Health, Beauty & Supplements',
    description: 'Vitamins, skincare, and personal care.',
    href: '/categories/health-beauty-and-supplements',
    icon: healthIcon,
  },
  {
    title: 'Home, Cleaning & Gardening',
    description: 'Cleaning supplies and home essentials.',
    href: '/categories/home-cleaning-and-gardening',
    icon: homeIcon,
  },
  {
    title: 'Baby Essentials',
    description: 'Nappies, wipes, and baby food.',
    href: '/categories/baby',
    icon: babyIcon,
  },
  {
    title: 'Pet Supplies',
    description: 'Food and treats for your furry friends.',
    href: '/categories/pet',
    icon: petIcon,
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
