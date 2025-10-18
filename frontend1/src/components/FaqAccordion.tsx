import React, { useState, useEffect } from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

interface FaqItem {
  question: string;
  answer: string;
}

interface FaqAccordionProps {
  page: string;
}

export function FaqAccordion({ page }: FaqAccordionProps) {
  const [faqs, setFaqs] = useState<FaqItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFaqs = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/faqs/?page=${page}`);
        if (!response.ok) {
          throw new Error('Failed to fetch FAQs');
        }
        const data: FaqItem[] = await response.json();
        setFaqs(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFaqs();
  }, [page]);

  if (isLoading) {
    return <div>Loading FAQs...</div>; // Or a skeleton loader
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return (
    <Accordion
      type="single"
      collapsible
      className="w-full"
    >
      {faqs.map((faq, index) => (
        <AccordionItem value={`item-${index + 1}`} key={index}>
          <AccordionTrigger>{faq.question}</AccordionTrigger>
          <AccordionContent className="flex flex-col gap-4 text-balance">
            <p>{faq.answer}</p>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}
