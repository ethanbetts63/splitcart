import React from 'react';
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

const faqsBySlug: Record<string, FaqItem[]> = {
  'meat-and-seafood': [
    {
      question: "Is it cheaper to buy meat at a supermarket or butcher?",
      answer: "It depends on the cut and the butcher. Common cheap cuts of meat are almost always cheaper at the big supermarkets but often a good local butcher will have more expensive cuts at a more competitive price. Not to mention a higher quality."
    },
    {
      question: "Is it cheaper to buy a whole chicken and cut it up, or buy the pieces separately?",
      answer: "It's considered on average to be around 30-50% cheaper to buy a full chicken. When you buy individual pieces such as the breast you are not just paying for the meat but also the labor required to separate and prepare the meat. On average 25-32% of a whole chicken is bone. But even this can be used to make stock or for flavor in soups."
    },
    {
      question: "What is the cheapest meat per kilo in Australia?",
      answer: "As of 2026 the cheapest per kilo price on meat was $3.45 per kg for chicken drumsticks in a bulk pack at aldi. Various other chicken pieces and a whole chicken can be as low as 4.20 - 4.50 per kg. Cheap Pork or beef sausages can be found for as little as $5.50 - $ per kilo. Cooking bacon can be found at 9 per kilo. Followed by corn beef silver side at 9.50 per kg. These two being the cheapest options for unprocessed boneless meat. Even factoring in that whole chickens and drumsticks are around 25 - 32% bone they are still significantly cheaper than any other option."
    },
    {
      question: "Is meat expensive in Australia?",
      answer: "Yes, meat is expensive in Australia. Australia is a major meat exporter, and high international demand drives up local prices as local consumers compete with overseas buyers. Additionally, the size of Australia adds significant transportation costs. Finally, strict regulations make it incredibly difficult for farmers and butchers to interact directly, necessitating a middle man that adds cost and creates a system more favorable to larger companies."
    },
    {
      question: "How do you compare prices?",
      answer: "Our price comparisons are based on all products shared by two companies in our system for a category. This 'product overlap' is why you'll sometimes see more items compared between companies like Coles and Woolworths then stores that have a more unique range, such as IGA or Aldi. Sometimes the range is so unique for a category that there is not enough product overlap to do a fair comparison. In such a case, we will omit the results entirely. Aldi, Coles and Woolworths generally have nationally consistant pricing but for IGA prices differ store to store, therefor we take the average price for IGA stores."
    },
  ],
  'fruit-and-veg': [
    {
      question: "Which australian supermarket has the freshest produce?",
      answer: "Coles and Woolworths stock their produce largely from the same suppliers. Aldi consistently wins Canstar blues fresh product award and is generally regarded online as being the best for customer satisfaction with regards to produce quality. However an honorouble mention would be IGA as IGA's are often locally sourced they can find freshness and quality that the bigger companies cannot compete with."
    },
    {
      question: "Are fruit and vegetables cheap in Australia?",
      answer: "Yes and no. Australia is generally regarded as having very high quality produce in comparison to other Western countries. In comparison to those countries with a similar quality Australias prices are very average. Many other countries have lower prices but rarely with such variety at a high quality. Australias proximity to south east asia is key. Australian produce prices are very seasonal."
    },
    {
      question: "What is the cheapest fruit per kilo in Australia?",
      answer: "Watermelon is consistently the most affordable fruit in Australia, with an average price of $2.63 per kg. While costs can range between $1.99 and $3.99 per kg depending on the retailer and season, it remains significantly cheaper than other popular staples. As a comparison, Oranges are the next most budget-friendly option ($3.32 per kg), followed by Bananas ($4.16 per kg), making Watermelon the clear choice for bulk value."
    },
    {
      question: "What is the cheapest vegetable in Australia per kilo?",
      answer: "Carrots rank as the cheapest vegetable in Australia, averaging just $1.47 per kg. They offer incredible value for money, with prices recorded as low as $0.79 per kg in some stores. They are followed by Potatoes ($2.00 per kg) and Onions ($2.42 per kg), confirming that root vegetables are generally the most economical fresh produce options available to Australian shoppers"
    },
    {
      question: "How do you compare prices?",
      answer: "Our price comparisons are based on all products shared by two companies in our system for a category. This 'product overlap' is why you'll sometimes see more items compared between companies like Coles and Woolworths then stores that have a more unique range, such as IGA or Aldi. Sometimes the range is so unique for a category that there is not enough product overlap to do a fair comparison. In such a case, we will omit the results entirely. Aldi, Coles and Woolworths generally have nationally consistant pricing but for IGA prices differ store to store, therefor we take the average price for IGA stores."
    },
  ],
  'snacks-and-sweets': [
    {
      question: "Why don't I see a \"cheaper at Aldi\" section above?",
      answer: "To say that a product is cheaper at Aldi than at Coles or Woolworths, Aldi would need to actually have that product. Aldi stocks somewhere around 1/3 to 1/5 as many products as Coles and Woolworths, and it stocks a very unique range of products. This makes direct comparisons very rare. This is why we have a substitution system. It solves this exact problem to help you take advantage of Aldi's generally cheaper products."
    },
    {
      question: "Is Aldi's \"Just Divine\" chocolate a good dupe for Cadbury blocks?",
      answer: "Aldi's Just Divine chocolate is widely considered one of the closest supermarket dupes to Cadbury. The texture is smoother and slightly less creamy, but the flavour profile is surprisingly similar — especially in the milk chocolate and hazelnut varieties. I would even say it tastes better. The biggest difference is the price: Just Divine is often 30–50% cheaper per 100g than Cadbury at Coles and Woolworths. If you want the classic Cadbury sweetness without paying full-brand pricing, Just Divine is one of Aldi's strongest value picks."
    },
    {
      question: "What are the best Aldi dupes for popular snacks in Australia?",
      answer: "Aldi is famous for creating low-cost versions of Australia's favourite snacks, and many of them hold up surprisingly well. Some of the best-known dupes include their Biscotto biscuits (Tim Tam dupe), Sprinters chips (Smith's/Kettle dupe), Just Divine chocolate (Cadbury dupe), Moser Roth (Lindt-style chocolate), and Meadows cookies (Coles/Woolworths bakery-style cookie dupe). These products usually cost noticeably less than the big brands, and while the flavour isn't always identical, the value per gram is often unbeatable."
    },
    {
      question: "How do you compare prices?",
      answer: "Our price comparisons are based on all products shared by two companies in our system for a category. This 'product overlap' is why you'll sometimes see more items compared between companies like Coles and Woolworths then stores that have a more unique range, such as IGA or Aldi. Sometimes the range is so unique for a category that there is not enough product overlap to do a fair comparison. In such a case, we will omit the results entirely. Aldi, Coles and Woolworths generally have nationally consistant pricing but for IGA prices differ store to store, therefor we take the average price for IGA stores."
    },
  ],
  'dairy-and-eggs': [
    {
      question: "Why have eggs gotten so expensive?",
      answer: "Egg prices have surged primarily due to the ongoing crisis of Highly Pathogenic Avian Influenza (HPAI), or bird flu, which has necessitated the culling of millions of egg-laying hens, severely reducing the national supply. This supply crunch, compounded by persistent general food inflation and higher transportation costs, has driven prices up significantly. The industry also faces a long recovery time, as it takes nearly five months for replacement hens to mature and begin regular production."
    },
    {
      question: "What's the price difference between caged, barn-laid and free-range eggs?",
      answer: "The difference in price directly reflects the complexity and cost of the production system. Caged eggs are the cheapest because they are the most space-efficient and cost-effective to produce. Barn-laid eggs are moderately more expensive than caged, as they require more space and labor, often leading to lower flock productivity. Free-range eggs are the most expensive, often costing 40% to 70% more than caged, due to the high costs associated with providing and maintaining outdoor access, higher land demands, and increased veterinary and labor requirements."
    },
    {
      question: "Is there a difference between home-brand milk and name-brand milk?",
      answer: "For plain milk, there's almost no practical difference. Blind taste tests show most people can't tell them apart, and all milk sold in Australia has to meet the same legal standards for fat, protein, and safety. The main difference is price: home-brand milk is usually much cheaper, while name brands mainly offer niche variants (A2, lactose-free, added calcium). For everyday use, home-brand milk is basically the same product at a better price."
    },
    {
      question: "Is Aldi's cheese as good as Coles or Woolworths?",
      answer: "It depends on the type of cheese. Aldi's basic block cheeses and sliced cheeses are generally solid and offer great value, but they don't always match the flavour depth of premium or branded options at Coles and Woolworths. For cooking or everyday sandwiches, Aldi is perfectly fine. For richer, specialty, or sharper cheeses, the big supermarkets' branded options tend to win."
    },
    {
      question: "Does Aldi have a good dupe for Lurpak or Western Star?",
      answer: "Yes — Aldi's \"Beautifully Butterfully\" butter is widely considered one of the best supermarket dupes for premium butters like Lurpak and Western Star. In taste tests it ranks surprisingly close, especially for spreading and general cooking. It's not identical, but it's extremely good for the price and one of Aldi's standout dairy products."
    },
    {
      question: "How do you compare prices?",
      answer: "Our price comparisons are based on all products shared by two companies in our system for a category. This 'product overlap' is why you'll sometimes see more items compared between companies like Coles and Woolworths then stores that have a more unique range, such as IGA or Aldi. Sometimes the range is so unique for a category that there is not enough product overlap to do a fair comparison. In such a case, we will omit the results entirely. Aldi, Coles and Woolworths generally have nationally consistant pricing but for IGA prices differ store to store, therefor we take the average price for IGA stores."
    },
  ],
  'pantry': [
    {
      question: "How much cheaper is it to make your own granola?",
      answer: "Homemade granola is typically 30–60% cheaper than store-bought versions from Coles, Woolworths, Aldi, or IGA. A simple batch using oats, nuts, seeds, and honey often costs $6–$10 per kilo, compared to packaged granolas that sell for $12–$20+ per kilo. You also control the sweetness, ingredients, and portion size."
    },
    {
      question: "What is the cheapest possible breakfast?",
      answer: "Across Australia's major supermarkets — Coles, Woolworths, Aldi, and IGA — the consistently cheapest breakfast is rolled oats. A bowl made with water or milk usually costs 20–40 cents per serve, making it one of the best value meals you can buy. Peanut butter toast, eggs on toast, and homemade granola are also affordable, but oats almost always win on cost per serving."
    },
    {
      question: "Is it cheaper to buy Asian sauces (soy, oyster, sriracha) at Coles, Woolworths, Aldi, or IGA compared to Asian grocers?",
      answer: "Asian grocers are usually the cheapest place to buy staple sauces like soy, oyster, and sriracha — especially if you prefer larger bottles or authentic imported brands. Prices per 100ml are often noticeably lower, and the range is wider. Among the big supermarkets, Aldi can be surprisingly competitive, especially for home-brand soy and oyster sauce. Coles and Woolworths can match or beat Asian grocers when specials are running, but at full price they're usually more expensive. IGA is the biggest wildcard: some stores are great, others are much pricier depending on location and supplier. If you want the lowest everyday price, Asian grocers generally win. For convenience or when Coles/Woolworths run good discounts, supermarkets can still be a strong option."
    },
    {
      question: "How do you compare prices?",
      answer: "Our price comparisons are based on all products shared by two companies in our system for a category. This 'product overlap' is why you'll sometimes see more items compared between companies like Coles and Woolworths then stores that have a more unique range, such as IGA or Aldi. Sometimes the range is so unique for a category that there is not enough product overlap to do a fair comparison. In such a case, we will omit the results entirely. Aldi, Coles and Woolworths generally have nationally consistant pricing but for IGA prices differ store to store, therefor we take the average price for IGA stores."
    },
  ],
  'bakery-and-deli': [
    {
      question: "What time do Coles and Woolworths mark down bakery items?",
      answer: "While specific times vary by store manager, most Australian supermarkets begin their bakery markdowns after 4:00 PM, with the steepest discounts (often up to 80%) occurring one hour before closing. Supermarkets are not legally required to discard bread daily, but they do so to maintain a 'fresh daily' standard."
    },
    {
      question: "Is it safe (and legal) for bakeries to sell yesterday's bread?",
      answer: "Yes, it is completely legal. According to Food Standards Australia New Zealand (FSANZ), there is no law forcing bakeries to bin bread at the end of the day unless it violates the '4-hour rule' for hazardous ingredients like meat or cream. If a bakery sells you a day-old baguette, they are complying with the law, provided it is not mouldy."
    },
    {
      question: "Which supermarket has the best food waste policy: Woolworths, Coles, or Aldi?",
      answer: "Each major retailer handles bakery waste differently. Woolworths partners with OzHarvest, while Coles utilizes SecondBite to redistribute unsold bread to community programs. Aldi's tighter supply chain results in less surplus, but they also partner with food relief agencies."
    },
    {
      question: "How much cheaper is it to bake your own bread?",
      answer: "Baking your own bread is often 40–70% cheaper than buying a loaf at Coles, Woolworths, Aldi, or IGA. A homemade loaf made from flour, yeast, salt, and water usually costs $1–$2, while supermarket loaves range from $3–$7+ depending on the brand and style. If you bake regularly or buy flour in bulk, the cost per loaf drops even further."
    },
    {
      question: "How do you compare prices?",
      answer: "Our price comparisons are based on all products shared by two companies in our system for a category. This 'product overlap' is why you'll sometimes see more items compared between companies like Coles and Woolworths then stores that have a more unique range, such as IGA or Aldi. Sometimes the range is so unique for a category that there is not enough product overlap to do a fair comparison. In such a case, we will omit the results entirely. Aldi, Coles and Woolworths generally have nationally consistant pricing but for IGA prices differ store to store, therefor we take the average price for IGA stores."
    },
  ],
  'home-cleaning-gardening-and-pets': [
    {
      question: "What is most important for toilet paper per kilo price, price per roll or ply count?",
      answer: "Focusing on ply count alone can be misleading, as lower-ply paper necessitates the use of more sheets per sitting, which quickly negates its lower cost. Conversely, while higher-ply paper is more expensive, its superior absorbency may lead to less consumption. The ideal metric for true value is the price per kilogram, as it accurately standardizes the amount of product purchased, though this figure is rarely provided by retailers. Honestly, if you are asking yourself this question it's probably time for a bidet."
    },
    {
      question: "Are brand name cleaning products really better than the home brand versions?",
      answer: "For many essential household cleaners, the performance difference between brand-name and home-brand versions is minimal or non-existent, especially for basic chemical compounds like bleach or common all-purpose sprays. Brand names often have a higher price due to extensive marketing and packaging, not necessarily superior quality. Tests have frequently shown that generic or store-brand products, especially in categories like multipurpose cleaner or dish soap, work just as effectively as the premium brands, allowing consumers to save between 30% and 60%. However, certain specialty products, such as heavy-duty trash bags or complex detergent formulations, are sometimes worth the extra cost for their superior strength, thickness, or specialized performance."
    },
    {
      question: "Is there a difference between home brand and name brand dishwashing tablets?",
      answer: "The performance difference between brand-name and home-brand dishwashing tablets is often present but generally marginal. While the most expensive tablets, particularly premium all-in-one formulations, may achieve a slightly superior wash, many home-brand or mid-tier alternatives offer comparable cleaning power for a fraction of the cost. The quality of the wash is often influenced less by the tablet brand and more significantly by the efficiency of the dishwasher itself and yes even proper dish stacking technique. Given this context, brand-name tablets are frequently an unjustifiably expensive choice, as the premium cost rarely delivers a proportionate increase in results."
    },
    {
      question: "How do you compare prices?",
      answer: "Our price comparisons are based on all products shared by two companies in our system for a category. This 'product overlap' is why you'll sometimes see more items compared between companies like Coles and Woolworths then stores that have a more unique range, such as IGA or Aldi. Sometimes the range is so unique for a category that there is not enough product overlap to do a fair comparison. In such a case, we will omit the results entirely. Aldi, Coles and Woolworths generally have nationally consistant pricing but for IGA prices differ store to store, therefor we take the average price for IGA stores."
    },
  ],
};

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

const PillarPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const faqs = slug ? (faqsBySlug[slug] ?? []) : [];

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
  let srcSet = undefined;
  let sizes = undefined;

  if (slug === 'meat-and-seafood') {
    imageUrl = meatImage;
  } else if (slug === 'fruit-and-veg') {
    imageUrl = fruitImage;
  } else if (slug === 'snacks-and-sweets') {
    imageUrl = snackImage;
  } else if (slug === 'dairy-and-eggs') {
    imageUrl = eggImage;
  } else if (slug === 'health-beauty-and-supplements') {
    imageUrl = shampooImage;
  } else if (slug === 'pantry') {
    imageUrl = survivalImage;
  } else if (slug === 'baby') {
    imageUrl = babyImage;
    srcSet = `${baby320} 320w, ${baby640} 640w, ${baby768} 768w, ${baby1024} 1024w, ${baby1280} 1280w`;
    sizes = "(min-width: 1024px) 50vw, 100vw";
  } else if (slug === 'bakery-and-deli') {
    imageUrl = bakeryImage;
    srcSet = `${bakery320} 320w, ${bakery640} 640w, ${bakery768} 768w, ${bakery1024} 1024w, ${bakery1280} 1280w`;
    sizes = "(min-width: 1024px) 50vw, 100vw";
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
        {faqs.length > 0 && (
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
