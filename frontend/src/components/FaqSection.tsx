import { Card, CardContent } from "./ui/card";
import { ChevronDown } from 'lucide-react';
import type { FaqSectionProps } from '@/types/FaqSectionProps';

export const FaqSection = ({ title, faqData }: FaqSectionProps) => {
  const jsonLd = faqData.length > 0
    ? {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: faqData.map((faq) => ({
          "@type": "Question",
          name: faq.question,
          acceptedAnswer: { "@type": "Answer", text: faq.answer },
        })),
      }
    : null;

  return (
    <>
      {jsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      )}
      <div className="py-8 bg-background">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center text-[var(--text-light-primary)] mb-8">{title}</h2>
          <div className="flex flex-col items-center gap-4">
            {faqData.map((faq, index) => (
              <div key={index} className="w-full md:w-2/3 lg:w-2/3">
                <Card className="bg-[var(--bg-light-primary)] text-[var(--text-dark-primary)] rounded-lg shadow-md">
                  <CardContent className="p-0">
                    <details className="group">
                      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-4 marker:hidden">
                        <h3 className="text-xl font-semibold text-[var(--text-dark-primary)]">{faq.question}</h3>
                        <ChevronDown className="h-6 w-6 shrink-0 text-[var(--text-dark-secondary)] transition-transform duration-300 group-open:rotate-180" />
                      </summary>
                      <div className="px-6 pb-6 pt-2">
                        <p className="text-[var(--text-dark-secondary)] text-lg">{faq.answer}</p>
                      </div>
                    </details>
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
