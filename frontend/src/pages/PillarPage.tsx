import React from 'react';
import { useParams } from 'react-router-dom';
import { useApiQuery } from '../hooks/useApiQuery';
import LoadingSpinner from '../components/LoadingSpinner';
import { ProductCarousel } from '../components/ProductCarousel';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../components/ui/accordion";
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
        {/* Product Carousels */}
        {pillarPage.primary_categories.map((category: PrimaryCategory, index: number) => (
                    <div key={category.slug} className="mb-8">
                      <ProductCarousel
                          key={category.slug}    title={category.name}
    sourceUrl="/api/products/"
    primaryCategorySlug={category.slug}
    pillarPageLinkSlug={slug}
    storeIds={storeIdsArray}
    slot={index}
    isDefaultStores={isDefaultStores}
/>
          </div>
        ))}

        {/* FAQ Section */}
        {pillarPage.faqs && pillarPage.faqs.length > 0 && (
          <div>
            <h2 className="text-3xl font-bold text-center mb-8">Frequently Asked Questions</h2>
            <Accordion type="single" collapsible className="w-full max-w-3xl mx-auto">
              {pillarPage.faqs.map((faq: FAQ, index: number) => (
                <AccordionItem value={`item-${index}`} key={index}>
                  <AccordionTrigger>{faq.question}</AccordionTrigger>
                  <AccordionContent>{faq.answer}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        )}
      </div>
    </div>
  );
};

export default PillarPage;
