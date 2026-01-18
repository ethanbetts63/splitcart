import React, { useState } from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";


import { Card, CardContent } from "./ui/card";

interface FaqItem {
  question: string;
  answer: string;
  pages: string[];
}

const allFaqs: FaqItem[] = [
  {"question": "Will I really save 10-15%?", "answer": "Hopefully! Our optimization aims to find the maximum possible savings. But it's restricted by the stores you choose, the items in you select and the substitutes you approve. Some shopping lists have more potential for savings than others, so individual results will vary but we find that 10-15% is a consistant average.", "pages": ["home"]},
  {"question": "What’s a ‘substitute’ and why does it matter?", "answer": "A substitute is a product you would be willing to have \"instead of\" the original product you choose. For example, a different brand of the same type of milk. Including substitutes gives our algorithm a lot more options to play with and is a major factor in the savings you should expect. We know it's an annoying to do but it's also the reason we can save you more than any other comparison site.", "pages": ["home", "substitutes"]},
  {"question": "Is it always cheaper than buying from one store?", "answer": "Splitting your cart is almost always cheaper, almost. Our results will always show you the \"Best Single Store\" option alongside the split-cart options, so you can clearly see if splitting your cart provides a real benefit for your specific shopping list.", "pages": ["home"]},
  {"question": "Which stores can I compare?", "answer": "Right now, SplitCart supports Coles, Woolworths, Aldi, and IGA. We’d love to bring the smaller guys on board too, but their price data is harder to track down — which hurts, because they’re often the real discount heroes.", "pages": ["home"]},
  {"question": "How accurate are the prices?", "answer": "The short answer is: pretty accurate! But not perfect. We pull prices directly from stores websites as often as we can but we can only be as accurate as the stores themselves.", "pages": ["home"]},
  {"question": "How can it be free?", "answer": "Great question!", "pages": ["home"]}
];

interface FaqProps {
  title: string;
  page: string;
  imageSrc: string;
  imageAlt: string;
  srcSet?: string;
  sizes?: string;
}

export const FAQ: React.FC<FaqProps> = ({ title, page, imageSrc, imageAlt, srcSet, sizes }) => {
  const [faqs] = useState<FaqItem[]>(allFaqs.filter(faq => faq.pages.includes(page)));

  const generateJsonLd = () => {
    if (!faqs.length) {
      return null;
    }

    const faqItems = faqs.map(faq => ({
      "@type": "Question",
      "name": faq.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.answer
      }
    }));

    const jsonLd = {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": faqItems
    };

    return (
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    );
  };

  return (
    <>
      {generateJsonLd()}
      <Card className="overflow-hidden p-0 border-0 shadow-none">
        <CardContent className="grid p-0 lg:grid-cols-2">
          <div className="p-6 lg:p-8 order-2 lg:order-1">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">{title}</h2>
            <Accordion
              type="single"
              collapsible
              className="w-full"
            >
              {faqs.map((faq, index) => (
                <AccordionItem value={`item-${index + 1}`} key={index} className="faq-item">
                  <AccordionTrigger>{faq.question}</AccordionTrigger>
                  <AccordionContent className="flex flex-col gap-4 text-balance">
                    <p>{faq.answer}</p>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
          <div className="relative flex items-center justify-center h-full order-1 lg:order-2">
            <img 
              src={imageSrc} 
              srcSet={srcSet}
              sizes={sizes}
              alt={imageAlt} 
              className="h-full w-full object-contain dark:brightness-[0.2] dark:grayscale" />
          </div>
        </CardContent>
      </Card>
    </>
  );
};
