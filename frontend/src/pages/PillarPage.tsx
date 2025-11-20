import React from 'react';
import { useParams } from 'react-router-dom';
import { useApiQuery } from '../hooks/useApiQuery';
import LoadingSpinner from '../components/LoadingSpinner';
import { ProductCarousel } from '../components/ProductCarousel';
import PriceComparisonChart from '../components/PriceComparisonChart';
import { FaqImageSection } from "../components/FaqImageSection"; // Added import
import confusedShopper from "../assets/confused_shopper.webp"; // Added import
import confusedShopper320 from "../assets/confused_shopper-320w.webp"; // Added import
import confusedShopper640 from "../assets/confused_shopper-640w.webp"; // Added import
import confusedShopper768 from "../assets/confused_shopper-768w.webp"; // Added import
import confusedShopper1024 from "../assets/confused_shopper-1024w.webp"; // Added import
import confusedShopper1280 from "../assets/confused_shopper-1280w.webp"; // Added import

import type { PrimaryCategory, FAQ, PillarPage as PillarPageType } from '../types';
import { useStoreList } from '../context/StoreListContext';

const PillarPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const DEFAULT_STORE_IDS = [
    515, 5123, 518, 523, 272, 276, 2197, 2198, 2199, 536, 5142, 547, 2218, 2219,
    2224, 5074, 5080, 5082, 5083, 5094, 5096, 5100, 498, 505, 254,
  ];
  const { selectedStoreIds } = useStoreList();
  const isDefaultStores = selectedStoreIds.size === 0;
  const storeIdsArray = React.useMemo(() =>
    isDefaultStores ? DEFAULT_STORE_IDS : Array.from(selectedStoreIds),
    [selectedStoreIds, isDefaultStores]
  );

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

  return (
    <div>
      {/* Hero Section */}
      <div className="relative h-96 bg-cover bg-center" style={{ backgroundImage: `url(${pillarPage.image_path})` }}>
        <div className="absolute inset-0 bg-black opacity-50"></div>
        <div className="relative z-10 flex flex-col items-center justify-center h-full text-white text-center">
          <h1 className="text-4xl font-bold">{pillarPage.hero_title}</h1>
          <p className="mt-4 max-w-2xl">{pillarPage.introduction_paragraph}</p>
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
                storeIds={storeIdsArray}
                slot={index}
                isDefaultStores={isDefaultStores}
            />
            {category.price_comparison_data && category.price_comparison_data.comparisons.length > 0 && (
              <div className="mt-4">
                {category.price_comparison_data.comparisons.map((comparison, compIndex) => (
                  <PriceComparisonChart key={compIndex} comparison={comparison} />
                ))}
              </div>
            )}
          </div>
        ))}

        {/* FAQ Section */}
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col gap-8">
            <section>
              <FaqImageSection
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
