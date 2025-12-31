import React, { useState, useEffect, useMemo } from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";
import { useAuth } from '../context/AuthContext';
import { Card, CardContent } from "./ui/card";
import { createApiClient } from '../services/apiClient';
import { fetchFaqsAPI } from '../services/faq.api';

interface FaqItem {
  question: string;
  answer: string;
}

interface FaqProps {
  title: string;
  page: string;
  imageSrc: string;
  imageAlt: string;
  srcSet?: string;
  sizes?: string;
}

export const FAQ: React.FC<FaqProps> = ({ title, page, imageSrc, imageAlt, srcSet, sizes }) => {
  const [faqs, setFaqs] = useState<FaqItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { token, anonymousId } = useAuth();

  const apiClient = useMemo(() => createApiClient(token, anonymousId), [token, anonymousId]);

  useEffect(() => {
    const fetchFaqs = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchFaqsAPI(apiClient, page);
        setFaqs(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFaqs();
  }, [page, apiClient]);

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
            {isLoading && <div>Loading FAQs...</div>}
            {error && <div className="text-red-500">Error: {error}</div>}
            {!isLoading && !error && (
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
            )}
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
