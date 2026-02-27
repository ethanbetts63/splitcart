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
import snackLineup from "../assets/snack_lineup.webp";
import snackLineup320 from "../assets/snack_lineup-320w.webp";
import snackLineup640 from "../assets/snack_lineup-640w.webp";
import snackLineup768 from "../assets/snack_lineup-768w.webp";
import snackLineup1024 from "../assets/snack_lineup-1024w.webp";
import snackLineup1280 from "../assets/snack_lineup-1280w.webp";
import bargainsImg from "../assets/bargains.webp";
import bargainsImg320 from "../assets/bargains-320w.webp";
import bargainsImg640 from "../assets/bargains-640w.webp";
import bargainsImg768 from "../assets/bargains-768w.webp";
import bargainsImg1024 from "../assets/bargains-1024w.webp";
import bargainsImg1280 from "../assets/bargains-1280w.webp";

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
        src: confusedShopper,
        srcSet: `${confusedShopper320} 320w, ${confusedShopper640} 640w, ${confusedShopper768} 768w, ${confusedShopper1024} 1024w, ${confusedShopper1280} 1280w`,
        sizes: "(max-width: 767px) 320px, (max-width: 1023px) 50vw, 33vw",
        alt: 'Shopper building a grocery list',
      },
    },
    {
      step: 2,
      title: 'Approve Substitutes.',
      description: "Tell us which alternatives you'd accept — a different brand of milk, a different cut of meat. More options means more savings.",
      image: {
        src: snackLineup,
        srcSet: `${snackLineup320} 320w, ${snackLineup640} 640w, ${snackLineup768} 768w, ${snackLineup1024} 1024w, ${snackLineup1280} 1280w`,
        sizes: "(max-width: 767px) 320px, (max-width: 1023px) 50vw, 33vw",
        alt: 'Lineup of snack products to choose between',
      },
    },
    {
      step: 3,
      title: 'See Your Savings.',
      description: 'We compare prices across Coles, Woolworths, Aldi and IGA and find the cheapest combination. Pick a split that works for you.',
      image: {
        src: bargainsImg,
        srcSet: `${bargainsImg320} 320w, ${bargainsImg640} 640w, ${bargainsImg768} 768w, ${bargainsImg1024} 1024w, ${bargainsImg1280} 1280w`,
        sizes: "(max-width: 767px) 320px, (max-width: 1023px) 50vw, 33vw",
        alt: 'Grocery bargains and savings',
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

      {/* --- Carousel: Snacks and Sweets --- */}
      <div className="container mx-auto px-4 py-8">
        <ProductCarousel
          key="snacks-and-sweets"
          title="Snacks & Sweets"
          sourceUrl="/api/products/"
          storeIds={anchorStoreIdsArray}
          primaryCategorySlugs={['snacks', 'sweets']}
          pillarPageLinkSlug="snacks-and-sweets"
          slot={0}
          isDefaultStores={isDefaultStores}
          isUserDefinedList={isUserDefinedList}
        />
      </div>

      {/* --- Letter Section --- */}
      <div className="container mx-auto px-4 md:px-16 pt-1 pb-1">
        <div className="text-center mb-8">
          <h2 className="text-5xl font-bold tracking-tight text-gray-900 max-w-2xl mx-auto">
            What percentage of a whole chicken is bone weight?
          </h2>
          <p className="text-xl mt-4">Short answer: <span className="font-bold">25-32%</span>. Most common answer: <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Who cares?</span></p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-12 text-lg ">
          <div className="flex flex-col gap-4">
            <p>
              <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">I care.</span> And if you're like me then you care too. If you're like me, you've considered the dollar value of a rewards point. Or weighed the merits of ply count versus the per kilo price of toilet paper.
            </p>
            <p className="font-bold">
              If you're like me then SplitCart was built for you. I know this to be a fact because I built SplitCart for me.
            </p>
            <p>
              The idea is simple. Why not buy each item in my shopping list from the store where it's cheapest? Becuase you don't know the price of every item in every store. Becuase you'd never go to ten stores on one shopping run. Becuase it would be a hassle.
            </p>
          </div>
          <div className="flex flex-col gap-4">
            <p>
              I've collected the prices. I've mathematically calculated the best two, three, or four store combinations, and I've removed as much hassle as humanly possible.
            </p>
            <p>
              So, welcome aboard fellow bargain hunter. I hope SplitCart can be as useful to you as it is to me. <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Expect to save 10-15%</span> on your grocery bill!
            </p>
            <p>
              If you have questions, suggestions or anything else I'd love to hear from you.
            </p>
            <div>
              <p>Happy hunting,</p>
              <p className="font-bold"><span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Ethan Betts</span>, <a href="mailto:ethanbetts63@gmail.com" className="text-blue-600 hover:underline">ethanbetts63@gmail.com</a></p>
              <p className="italic text-sm text-gray-600">Founder and Developer</p>
            </div>
          </div>
        </div>
      </div>

      {/* --- Carousels: Meat, Seafood / Eggs, Dairy --- */}
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <ProductCarousel
            key="meat-and-seafood"
            title="Meat & Seafood"
            sourceUrl="/api/products/"
            storeIds={anchorStoreIdsArray}
            primaryCategorySlugs={['meat', 'seafood']}
            pillarPageLinkSlug="meat-and-seafood"
            slot={1}
            isDefaultStores={isDefaultStores}
          isUserDefinedList={isUserDefinedList}
          />
          <ProductCarousel
            key="dairy"
            title="Dairy"
            sourceUrl="/api/products/"
            storeIds={anchorStoreIdsArray}
            primaryCategorySlugs={['dairy']}
            pillarPageLinkSlug="dairy"
            slot={2}
            isDefaultStores={isDefaultStores}
          isUserDefinedList={isUserDefinedList}
          />
        </div>
      </div>
      
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
