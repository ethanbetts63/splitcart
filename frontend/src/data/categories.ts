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

export const CATEGORY_SLUGS = [
  'snacks-and-sweets',
  'meat-and-seafood',
  'dairy-and-eggs',
  'fruit-and-veg',
  'pantry',
  'international-herbs-and-spices',
  'bakery-and-deli',
  'drinks',
  'health-beauty-and-supplements',
  'home-cleaning-gardening-and-pets',
  'baby',
] as const;

export type CategorySlug = (typeof CATEGORY_SLUGS)[number];

type CategoryEntry = {
  title: string;
  description: string;
  href: string;
  icon: string;
  featured?: boolean;
};

const ALL_CATEGORIES: CategoryEntry[] = [
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

const bargains = ALL_CATEGORIES.find((c) => c.featured);
const others = ALL_CATEGORIES.filter((c) => !c.featured).sort((a, b) =>
  a.title.localeCompare(b.title)
);

export const CATEGORIES = bargains ? [bargains, ...others] : others;
