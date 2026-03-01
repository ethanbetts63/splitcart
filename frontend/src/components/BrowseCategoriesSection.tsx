import { Link } from 'react-router-dom';

import bargainsIcon from '../assets/food_svgs/Tools-Kitchen-Scale--Streamline-Ultimate.svg';
import snacksSweetsIcon from '../assets/food_svgs/Ice-Cream-Cone--Streamline-Ultimate.svg';
import meatIcon from '../assets/food_svgs/Seafood-Squid--Streamline-Ultimate.svg';
import dairyIcon from '../assets/food_svgs/Animal-Products-Egg--Streamline-Ultimate.svg';
import fruitVegIcon from '../assets/food_svgs/Fruit-Watermelon--Streamline-Ultimate.svg';
import internationalSpiceIcon from '../assets/food_svgs/Seafood-Sushi--Streamline-Ultimate.svg';
import pantryIcon from '../assets/food_svgs/Pasta-Bowl-Warm--Streamline-Ultimate.svg';
import bakeryIcon from '../assets/food_svgs/Bread-Loaf--Streamline-Ultimate.svg';
import drinksIcon from '../assets/food_svgs/Champagne-Cooler--Streamline-Ultimate.svg';
import healthIcon from '../assets/food_svgs/Water-Bottle-Glass--Streamline-Ultimate.svg';
import homeIcon from '../assets/food_svgs/Kitchenware-Spatula-1--Streamline-Ultimate.svg';
import babyIcon from '../assets/food_svgs/Coffee-Cold--Streamline-Ultimate.svg';

const rawCategories = [
  {
    title: 'Bargains',
    description: 'The biggest discounts across all stores.',
    href: '/bargains',
    icon: bargainsIcon,
    featured: true,
  },
  {
    title: 'Snacks & Sweets',
    description: 'Chips, chocolate, lollies, and biscuits.',
    href: '/categories/snacks-and-sweets',
    icon: snacksSweetsIcon,
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
    title: 'Pantry',
    description: 'Staples, sauces, and canned goods.',
    href: '/categories/pantry',
    icon: pantryIcon,
  },
  {
    title: 'International, Herbs & Spices',
    description: 'Global foods, seasonings, and spices.',
    href: '/categories/international-herbs-and-spices',
    icon: internationalSpiceIcon,
  },
  {
    title: 'Bakery & Deli',
    description: 'Bread, pastries, and cured meats.',
    href: '/categories/bakery-and-deli',
    icon: bakeryIcon,
  },
  {
    title: 'Drinks',
    description: 'Soft drinks, juice, beer, and wine.',
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
    title: 'Home, Cleaning, Gardening & Pets',
    description: 'Household goods, pet food, and more.',
    href: '/categories/home-cleaning-gardening-and-pets',
    icon: homeIcon,
  },
  {
    title: 'Baby Essentials',
    description: 'Nappies, wipes, and baby food.',
    href: '/categories/baby',
    icon: babyIcon,
  },
];

const bargains = rawCategories.find(c => c.title === 'Bargains');
const others = rawCategories
  .filter(c => c.title !== 'Bargains')
  .sort((a, b) => a.title.localeCompare(b.title));

const categories = bargains ? [bargains, ...others] : others;

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
