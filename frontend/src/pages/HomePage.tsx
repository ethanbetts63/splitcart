import React from 'react'; 
import { ProductCarousel } from "../components/ProductCarousel";
import { FAQ } from "../components/FAQ";
import { useStoreList } from "../context/StoreListContext";
import { AspectRatio } from "../components/ui/aspect-ratio";
import confusedShopper from "../assets/confused_shopper.webp";
import confusedShopper320 from "../assets/confused_shopper-320w.webp";
import confusedShopper640 from "../assets/confused_shopper-640w.webp";
import confusedShopper768 from "../assets/confused_shopper-768w.webp";
import confusedShopper1024 from "../assets/confused_shopper-1024w.webp";
import confusedShopper1280 from "../assets/confused_shopper-1280w.webp";
import kingKongImage from "../assets/king_kong.webp";
import kingKongImage320 from "../assets/king_kong-320w.webp";
import kingKongImage640 from "../assets/king_kong-640w.webp";
import kingKongImage768 from "../assets/king_kong-768w.webp";
import kingKongImage1024 from "../assets/king_kong-1024w.webp";
import kingKongImage1280 from "../assets/king_kong-1280w.webp";

import Seo from '../components/Seo';
import { HowItWorksSection } from '../components/HowItWorksSection';
import { BrowseCategoriesSection } from '../components/BrowseCategoriesSection';
import { FounderLetterSection } from '../components/FounderLetterSection';
import listImg from "../assets/list.png";
import listImg320 from "../assets/list-320w.webp";
import listImg640 from "../assets/list-640w.webp";
import listImg768 from "../assets/list-768w.webp";
import listImg1024 from "../assets/list-1024w.webp";
import listImg1280 from "../assets/list-1280w.webp";
import sizeComparison from "../assets/size_comparison.png";
import sizeComparison320 from "../assets/size_comparison-320w.webp";
import sizeComparison640 from "../assets/size_comparison-640w.webp";
import sizeComparison768 from "../assets/size_comparison-768w.webp";
import sizeComparison1024 from "../assets/size_comparison-1024w.webp";
import sizeComparison1280 from "../assets/size_comparison-1280w.webp";
import moneyImg from "../assets/money.png";
import moneyImg320 from "../assets/money-320w.webp";
import moneyImg640 from "../assets/money-640w.webp";
import moneyImg768 from "../assets/money-768w.webp";
import moneyImg1024 from "../assets/money-1024w.webp";
import moneyImg1280 from "../assets/money-1280w.webp";

const homeFaqs = [
  {"question": "Will I really save 10-15%?", "answer": "Hopefully! Our optimization aims to find the maximum possible savings. But it's restricted by the stores you choose, the items in you select and the substitutes you approve. Some shopping lists have more potential for savings than others, so individual results will vary but we find that 10-15% is a consistant average."},
  {"question": "What’s a ‘substitute’ and why does it matter?", "answer": "A substitute is a product you would be willing to have \"instead of\" the original product you choose. For example, a different brand of the same type of milk. Including substitutes gives our algorithm a lot more options to play with and is a major factor in the savings you should expect. We know it's an annoying to do but it's also the reason we can save you more than any other comparison site."},
  {"question": "Is it always cheaper than buying from one store?", "answer": "Splitting your cart is almost always cheaper, almost. Our results will always show you the \"Best Single Store\" option alongside the split-cart options, so you can clearly see if splitting your cart provides a real benefit for your specific shopping list."},
  {"question": "Which stores can I compare?", "answer": "Right now, SplitCart supports Coles, Woolworths, Aldi, and IGA. We’d love to bring the smaller guys on board too, but their price data is harder to track down — which hurts, because they’re often the real discount heroes."},
  {"question": "How accurate are the prices?", "answer": "The short answer is: pretty accurate! But not perfect. We pull prices directly from stores websites as often as we can but we can only be as accurate as the stores themselves."},
  {"question": "How can it be free?", "answer": "Great question!"}
];

const HomePage = () => {
  const { selectedStoreIds, anchorStoreMap, isUserDefinedList } = useStoreList();

  const webSiteSchema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "SplitCart",
    "url": "https://www.splitcart.com.au",
    "founder": {
      "@type": "Person",
      "name": "Ethan Betts"
    },
    "potentialAction": {
        "@type": "SearchAction",
        "target": {
            "@type": "EntryPoint",
            "urlTemplate": "https://www.splitcart.com.au/search?q={search_term_string}"
        },
        "query-input": "required name=search_term_string"
    }
  };

  const isDefaultStores = !isUserDefinedList;

  const howItWorksSteps = [
    {
      step: 1,
      title: 'Build Your List.',
      description: 'Search or browse and add items to your cart. The bigger and more specific your list, the more we can save you.',
      image: {
        src: listImg,
        srcSet: `${listImg320} 320w, ${listImg640} 640w, ${listImg768} 768w, ${listImg1024} 1024w, ${listImg1280} 1280w`,
        sizes: "(max-width: 767px) 320px, (max-width: 1023px) 50vw, 33vw",
        alt: 'Grocery list with bag of shopping',
      },
    },
    {
      step: 2,
      title: 'Approve Substitutes.',
      description: "Tell us which alternatives you'd accept — a different brand of milk, a different cut of meat. More options means more savings.",
      image: {
        src: sizeComparison,
        srcSet: `${sizeComparison320} 320w, ${sizeComparison640} 640w, ${sizeComparison768} 768w, ${sizeComparison1024} 1024w, ${sizeComparison1280} 1280w`,
        sizes: "(max-width: 767px) 320px, (max-width: 1023px) 50vw, 33vw",
        alt: 'Price comparison between products',
      },
    },
    {
      step: 3,
      title: 'See Your Savings.',
      description: 'We compare prices across Coles, Woolworths, Aldi and IGA and find the cheapest combination. Pick a split that works for you.',
      image: {
        src: moneyImg,
        srcSet: `${moneyImg320} 320w, ${moneyImg640} 640w, ${moneyImg768} 768w, ${moneyImg1024} 1024w, ${moneyImg1280} 1280w`,
        sizes: "(max-width: 767px) 320px, (max-width: 1023px) 50vw, 33vw",
        alt: 'Money bag representing savings',
      },
    },
  ];

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

  return (
    <div>
      <Seo
        title="SplitCart: Australian Grocery Price Comparison"
        description="Every store has a deal — but finding them all takes forever. SplitCart automates discount hunting by comparing prices across Coles, Woolworths, Aldi and IGA and splitting your cart for the cheapest overall shop. One list, multiple stores, maximum savings."
        canonicalPath="/"
        structuredData={webSiteSchema}
      />
      {/* --- Hero Section --- */}
      <div className="container mx-auto px-4 pt-4 pb-1">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div>
            <AspectRatio ratio={16 / 9}>
              <img 
                src={confusedShopper} 
                srcSet={`${confusedShopper320} 320w, ${confusedShopper640} 640w, ${confusedShopper768} 768w, ${confusedShopper1024} 1024w, ${confusedShopper1280} 1280w`}
                sizes="(min-width: 1024px) 50vw, calc(100vw - 2rem)"
                alt="Confused Shopper" 
                className="rounded-md object-cover w-full h-full"
                fetchPriority="high" />
            </AspectRatio>
          </div>
          <div className="text-left">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
              Find the Cheapest Way to Buy Your Entire Grocery List.
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Every supermarket has deals — just not on the same items. SplitCart compares prices across Coles, Woolworths, Aldi and IGA and <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">splits your cart for the cheapest possible shop.</span>
            </p>
          </div>
        </div>
      </div>

      {/* --- Browse by Category --- */}
      <BrowseCategoriesSection />

      {/* --- How It Works Section --- */}
      <HowItWorksSection steps={howItWorksSteps} />

      {/* --- Carousel: Bargains --- */}
      <div className="container mx-auto px-4 py-8">
        <ProductCarousel
          key="bargains"
          title="Bargains"
          sourceUrl="/api/products/bargain-carousel/"
          storeIds={anchorStoreIdsArray}
          isDefaultStores={isDefaultStores}
          isUserDefinedList={isUserDefinedList}
        />
      </div>

      {/* --- Letter Section --- */}
      <FounderLetterSection />

      {/* --- FAQ Section --- */}
      <div className="container mx-auto px-4 py-8">
        <section>
          <FAQ
            title="The Hard Hitting Questions"
            faqs={homeFaqs}
            imageSrc={kingKongImage}
            srcSet={`${kingKongImage320} 320w, ${kingKongImage640} 640w, ${kingKongImage768} 768w, ${kingKongImage1024} 1024w, ${kingKongImage1280} 1280w`}
            sizes="(min-width: 1024px) 50vw, calc(100vw - 2rem)"
            imageAlt="King Kong swatting at discount planes"
          />
        </section>
      </div>

    </div>
  );
};

export default HomePage;
