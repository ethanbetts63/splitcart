import { ProductCarousel } from '../components/ProductCarousel';
import PriceComparisonChart from '../components/PriceComparisonChart';
import { FaqSection } from "../components/FaqSection";
import { faqsBySlug } from '@/data/pillar-faqs';
import confusedShopper from "../assets/confused_shopper.webp";
import meatImage from '../assets/fish_meat_box.webp';
import snackImage from '../assets/snack_lineup.webp';
import eggImage from '../assets/egg_frying.webp';
import shampooImage from '../assets/shampoo.webp';
import survivalImage from '../assets/survival.webp';
import { AspectRatio } from '../components/ui/aspect-ratio';
import type { PrimaryCategory, PillarPage as PillarPageType, Product } from '../types';
import { assetSrc, assetSrcSet, type ImageAsset } from '@/lib/assets';

import babyImage from '../assets/baby-1024w.webp';
import baby320 from '../assets/baby-320w.webp';
import baby640 from '../assets/baby-640w.webp';
import baby768 from '../assets/baby-768w.webp';
import baby1024 from '../assets/baby-1024w.webp';
import baby1280 from '../assets/baby-1280w.webp';

import bakeryImage from '../assets/bread_dollar-1024w.webp';
import bakery320 from '../assets/bread_dollar-320w.webp';
import bakery640 from '../assets/bread_dollar-640w.webp';
import bakery768 from '../assets/bread_dollar-768w.webp';
import bakery1024 from '../assets/bread_dollar-1024w.webp';
import bakery1280 from '../assets/bread_dollar-1280w.webp';

import fruitDollar320 from '../assets/fruit_dollar-320w.webp';
import fruitDollar640 from '../assets/fruit_dollar-640w.webp';
import fruitDollar768 from '../assets/fruit_dollar-768w.webp';
import fruitDollar1024 from '../assets/fruit_dollar-1024w.webp';
import fruitDollar1280 from '../assets/fruit_dollar-1280w.webp';

type SlugImageConfig = {
  asset: ImageAsset;
  srcSet?: string;
  sizes?: string;
};

const SLUG_IMAGES: Record<string, SlugImageConfig> = {
  'meat-and-seafood': { asset: meatImage },
  'fruit-and-veg': {
    asset: fruitDollar1024,
    srcSet: assetSrcSet([[fruitDollar320, 320], [fruitDollar640, 640], [fruitDollar768, 768], [fruitDollar1024, 1024], [fruitDollar1280, 1280]]),
    sizes: "(min-width: 1024px) 50vw, 100vw",
  },
  'snacks-and-sweets': { asset: snackImage },
  'dairy-and-eggs': { asset: eggImage },
  'health-beauty-and-supplements': { asset: shampooImage },
  'pantry': { asset: survivalImage },
  'baby': {
    asset: babyImage,
    srcSet: assetSrcSet([[baby320, 320], [baby640, 640], [baby768, 768], [baby1024, 1024], [baby1280, 1280]]),
    sizes: "(min-width: 1024px) 50vw, 100vw",
  },
  'bakery-and-deli': {
    asset: bakeryImage,
    srcSet: assetSrcSet([[bakery320, 320], [bakery640, 640], [bakery768, 768], [bakery1024, 1024], [bakery1280, 1280]]),
    sizes: "(min-width: 1024px) 50vw, 100vw",
  },
};

type PillarPageProps = {
  pillarPage: PillarPageType;
  slug: string;
  categoryProducts?: Record<string, Product[]>;
};

const PillarPage = ({ pillarPage, slug, categoryProducts = {} }: PillarPageProps) => {
  const faqs = faqsBySlug[slug] ?? [];
  const { asset: imageUrl, srcSet, sizes } = SLUG_IMAGES[slug] ?? { asset: confusedShopper };

  return (
    <div>
      {/* --- Hero Section --- */}
      <div className="container mx-auto px-4 pt-4 pb-1">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div>
            <AspectRatio ratio={16 / 9}>
              <img
                src={assetSrc(imageUrl)}
                srcSet={srcSet}
                sizes={sizes}
                alt={pillarPage.hero_title}
                className="rounded-md object-cover w-full h-full"
                fetchPriority="high" />
            </AspectRatio>
          </div>
          <div className="text-left">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
              {pillarPage.hero_title}
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              {pillarPage.introduction_paragraph}
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Product Carousels and Price Comparisons */}
        {pillarPage.primary_categories.map((category: PrimaryCategory, index: number) => (
          <div key={category.slug} className="mb-8">
            <ProductCarousel
                title={category.name}
                sourceUrl="/api/products/"
                products={categoryProducts[category.slug]}
                primaryCategorySlugs={[category.slug]}
                pillarPageLinkSlug={slug}
                slot={index}
            />
            {category.price_comparison_data && category.price_comparison_data.comparisons && category.price_comparison_data.comparisons.length > 0 && (
              <>
                <h2 className="text-3xl font-bold text-center my-8">
                  Where to buy <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">cheap</span>  {category.name} in Australia?
                </h2>
                <div className="mt-4 flex flex-wrap -mx-2">
                  {category.price_comparison_data.comparisons.map((comparison, compIndex) => (
                    <div key={compIndex} className="w-full lg:w-1/2 px-2 mb-4">
                      <PriceComparisonChart comparison={comparison} categoryName={category.name} />
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        ))}

        {/* FAQ Section */}
        {faqs.length > 0 && (
          <div className="container mx-auto px-4 py-8">
            <div className="flex flex-col gap-8">
              <section>
                <FaqSection
                  title={`Frequently Asked Questions about ${pillarPage.hero_title}`}
                  faqData={faqs}
                />
              </section>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PillarPage;
