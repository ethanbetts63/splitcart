import React, { useState } from 'react';
import { Card, CardContent } from "./ui/card";
import { ChevronDown } from 'lucide-react';
import type { FaqV2Props } from '../types/FaqV2Props';

export const FaqV2: React.FC<FaqV2Props> = ({ title, faqs }) => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggleFaq = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

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
      <div className="pt-10 pb-2">
        <div className="container mx-auto px-0 md:px-4">
          <h2 className="text-4xl font-bold text-center text-black mb-8">{title}</h2>
          <div className="flex flex-col items-center gap-4">
            {faqs.map((faq, index) => (
              <div key={index} className="w-full md:w-2/3">
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
