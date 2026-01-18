import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useApiQuery } from '../hooks/useApiQuery';
import LoadingSpinner from '../components/LoadingSpinner';
import { ProductCarousel } from '../components/ProductCarousel';
import PriceComparisonChart from '../components/PriceComparisonChart';
import { FaqV2 } from "../components/FaqV2"; 
import type { FaqItem } from '@/types';
import confusedShopper from "../assets/confused_shopper.webp"; 
import meatImage from '../assets/fish_meat_box.webp';
import fruitImage from '../assets/fruit_detectives.webp';
import snackImage from '../assets/snack_lineup.webp';
import eggImage from '../assets/egg_frying.webp';
import shampooImage from '../assets/shampoo.webp';
import survivalImage from '../assets/survival.webp';
import { AspectRatio } from '../components/ui/aspect-ratio';
import type { PrimaryCategory, PillarPage as PillarPageType } from '../types';
import { useStoreList } from '../context/StoreListContext';

const PillarPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [faqs, setFaqs] = useState<FaqItem[]>([]);

  useEffect(() => {
    const loadFaqs = async () => {
      if (slug) {
        try {
          // Dynamically import the faq module based on the slug
          const module = await import(`../data/pillar-page-faqs/${slug}.ts`);
          setFaqs(module.faqs);
        } catch (error) {
          console.error(`Failed to load FAQs for slug: ${slug}`, error);
          setFaqs([]); // Reset or handle error state
        }
      }
    };
    loadFaqs();
  }, [slug]);

  const { selectedStoreIds, anchorStoreMap, isUserDefinedList } = useStoreList();
  
  const anchorStoreIdsArray = React.useMemo(() => {
    if (!anchorStoreMap) {
      return Array.from(selectedStoreIds);
    }
    const anchorIds = new Set<number>();
    for (const storeId of selectedStoreIds) {
      const anchorId = anchorStoreMap[storeId];
      if (anchorId) {
        anchorIds.add(anchorId);
      }
    }
    return Array.from(anchorIds);
  }, [selectedStoreIds, anchorStoreMap]);

  const isDefaultStores = !isUserDefinedList;


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

                </div>
              </>
            )}
          </div>
        ))}

        {/* FAQ Section */}
        {faqs && faqs.length > 0 && (
          <div className="container mx-auto px-4 py-8">
            <div className="flex flex-col gap-8">
              <section>
                <FaqV2
                  title={`Frequently Asked Questions about ${pillarPage.hero_title}`}
                  faqs={faqs}
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
