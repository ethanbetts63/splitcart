import React from 'react';
import { useParams } from 'react-router-dom';
import { useApiQuery } from '../hooks/useApiQuery';
import LoadingSpinner from '../components/LoadingSpinner';
import { ProductCarousel } from '../components/ProductCarousel';
import PriceComparisonChart from '../components/PriceComparisonChart';
import { FAQ } from "../components/FAQ"; 
import confusedShopper from "../assets/confused_shopper.webp"; 
import confusedShopper320 from "../assets/confused_shopper-320w.webp"; 
import confusedShopper640 from "../assets/confused_shopper-640w.webp"; 
import confusedShopper768 from "../assets/confused_shopper-768w.webp"; 
import confusedShopper1024 from "../assets/confused_shopper-1024w.webp"; 
import confusedShopper1280 from "../assets/confused_shopper-1280w.webp"; 
import meatImage from '../assets/fish_meat_box.webp';
import fruitImage from '../assets/fruit_detectives.webp';
import snackImage from '../assets/snack_lineup.webp';
import eggImage from '../assets/egg_frying.webp';
import shampooImage from '../assets/shampoo.webp';
import survivalImage from '../assets/survival.webp';

import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { AspectRatio } from '../components/ui/aspect-ratio';
import type { PrimaryCategory, PillarPage as PillarPageType } from '../types';
import { useStoreList } from '../context/StoreListContext';

const PillarPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const DEFAULT_ANCHOR_IDS = [105, 458, 549, 504, 562, 4186];

  const { selectedStoreIds, anchorStoreMap } = useStoreList();
  const isDefaultStores = selectedStoreIds.size === 0;

  const anchorStoreIdsArray = React.useMemo(() => {
    if (isDefaultStores) {
      return DEFAULT_ANCHOR_IDS;
    }
    const anchorIds = new Set<number>();
    for (const storeId of selectedStoreIds) {
      const anchorId = anchorStoreMap[storeId];
      if (anchorId) {
        anchorIds.add(anchorId);
      }
    }
    // Fallback to default if the mapping results in an empty list
    return anchorIds.size > 0 ? Array.from(anchorIds) : DEFAULT_ANCHOR_IDS;
  }, [selectedStoreIds, anchorStoreMap, isDefaultStores]);


  const {
    data: pillarPage,
    isLoading,
    isError,
  } = useApiQuery<PillarPageType>(
    ['pillarPage', slug],
    `/api/pillar-pages/${slug}/`,
    {},
    { enabled: !!slug }
  );

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (isError || !pillarPage) {
    return (
      <div className="text-center py-10">
        <h2 className="text-2xl font-bold">Page Not Found</h2>
        <p>The page you are looking for does not exist.</p>
      </div>
    );
  }

  let imageUrl;
  if (slug === 'meat-and-seafood') {
    imageUrl = meatImage;
  } else if (slug === 'fruit-veg-and-spices') {
    imageUrl = fruitImage;
  } else if (slug === 'snacks-and-sweets') {
    imageUrl = snackImage;
  } else if (slug === 'eggs-and-dairy') {
    imageUrl = eggImage;
  } else if (slug === 'health-beauty-and-supplements') {
    imageUrl = shampooImage;
  } else if (slug === 'pantry-and-international') {
    imageUrl = survivalImage;
  } else {
    imageUrl = confusedShopper;
  }


  return (
    <div>
      {/* --- Hero Section --- */}
      <div className="container mx-auto px-4 pt-4 pb-1">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div>
            <AspectRatio ratio={16 / 9}>
              <img 
                src={imageUrl} 
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
                primaryCategorySlugs={[category.slug]}
                pillarPageLinkSlug={slug}
                storeIds={anchorStoreIdsArray}
                slot={index}
                isDefaultStores={isDefaultStores}
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
                  <div className="w-full lg:w-1/2 px-2 mb-4">
                    <Card className="h-full">
                      <CardHeader>
                        <CardTitle>How We Compare</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-700">
                          Our price comparisons are based on all products shared by two companies in our system for a category. This 'product overlap' is why you'll sometimes see more items compared between companies like Coles and Woolworths then stores that have a more unique range, such as IGA or Aldi. Sometimes the range is so unique for a category that there is not enough product overlap to do a fair comparison. In such a case, we will omit the results entirely. Aldi, Coles and Woolworths generally have nationally consistant pricing but for IGA prices differ store to store, therefor we take the average price for IGA stores. 
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </>
            )}
          </div>
        ))}

        {/* FAQ Section */}
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col gap-8">
            <section>
              <FAQ
                title={`Frequently Asked Questions about ${pillarPage.hero_title}`}
                page={slug || 'general'} // Use slug for page prop
                imageSrc={confusedShopper}
                srcSet={`${confusedShopper320} 320w, ${confusedShopper640} 640w, ${confusedShopper768} 768w, ${confusedShopper1024} 1024w, ${confusedShopper1280} 1280w`}
                sizes="(min-width: 1024px) 50vw, 100vw"
                imageAlt="Confused Shopper"
              />
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PillarPage;
