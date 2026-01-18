import React, { useState } from 'react';
import { Card, CardContent } from "./ui/card";
import type { FaqItem } from '@/types';
import { ChevronDown } from 'lucide-react';

// Hardcoded FAQ data for the homepage
const homeFaqs: FaqItem[] = [
  {
    "question": "Will I get reminders or confirmations?",
    "answer": "You will receive a reminder email 1 week and 1 day before the delivery date. They are not confirmation emails so you do not need to respond. They are simply to remind you."
  },
  {
    "question": "What is your refund policy?",
    "answer": "We can’t unsend flowers. But everything up until that point is fair game."
  },
  {
    "question": "Can I increase or decrease the budget later?",
    "answer": "Yes you can. For subscriptions this is as simple as increasing the subscription amount. For upfront payment plans, by lowering the cost of each bouquet we can increase the frequency or duration of the plan. By increasing the cost of each bouquet, we can do the opposite, or you can top off the amount, to maintain or increase the quality of the bouquets."
  },
  {
    "question": "What countries do you operate in?",
    "answer": "Currently we operate in the EU (Europe), United Kingdom, North America (USA & Canada), Australia and New Zealand."
  },
  {
    "question": "Is delivery included in the price?",
    "answer": "Cost of delivery is included in your yearly flower budget. Our service fee is placed seperately on top for transparency."
  }
];

interface FaqV2Props {
  title: string;
}

export const FaqV2: React.FC<FaqV2Props> = ({ title }) => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggleFaq = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  const generateJsonLd = () => {
    if (!homeFaqs.length) {
      return null;
    }

    const faqItems = homeFaqs.map(faq => ({
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
      <div className="pt-10 pb-2">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center text-black mb-8">{title}</h2>
          <div className="flex flex-col items-center gap-4">
            {homeFaqs.map((faq, index) => (
              <div key={index} className="w-full md:w-2/3 lg:w-2/3">
                <Card className="bg-white text-gray-900 rounded-lg shadow-lg border-0">
                  <CardContent className="p-0">
                    <div
                      className="flex justify-between items-center p-4 cursor-pointer"
                      onClick={() => toggleFaq(index)}
                    >
                      <h3 className="text-xl font-semibold text-black">{faq.question}</h3>
                      <ChevronDown
                        className={`h-6 w-6 text-gray-500 transition-transform duration-300 ${openIndex === index ? 'transform rotate-180' : ''
                          }`}
                      />
                    </div>
                    <div
                      className={`overflow-hidden transition-all ease-in-out duration-500 ${
                        openIndex === index ? 'max-h-96' : 'max-h-0'
                      }`}
                    >
                      <div className="px-6 pb-6 pt-2">
                        <p className="text-gray-600 text-lg">{faq.answer}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
};
