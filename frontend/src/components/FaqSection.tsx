import { Card, CardContent } from './common/card';
import { ChevronDown } from 'lucide-react';
import type { FaqSectionProps } from '@/types/FaqSectionProps';
import { buildFaqSchema } from '@/lib/seo';
import StructuredDataScript from '@/components/seo/StructuredDataScript';

export const FaqSection = ({ title, faqData }: FaqSectionProps) => {
  // All JSON-LD goes through the one escaped emitter. This component used to
  // build its own `<script>` with a bare `JSON.stringify`, one of four such
  // paths in the repo and none of them escaping `<`. See seo-standard.md
  // section 3 (SEO-7).
  const faqSchema = buildFaqSchema(faqData);

  // The five colours below were `text-[var(--text-light-primary)]` and four
  // siblings -- tokens declared nowhere in this repo. An unresolvable var()
  // invalidates the whole declaration rather than just the value, so the
  // heading, the card, the question and the answer all rendered at whatever
  // they inherited, and nothing anywhere reported it. The names said what they
  // wanted (primary text, a light surface, secondary text); those are the
  // roles used here. `npm run check:tokens` fails on a dangling read now.
  return (
    <>
      <StructuredDataScript structuredData={faqSchema} />
      <div className="py-8 bg-surface-page">
        <div className="site-shell">
          <h2 className="text-title font-bold text-center text-text-primary mb-8">{title}</h2>
          <div className="flex flex-col items-center gap-4">
            {faqData.map((faq, index) => (
              <div key={index} className="w-full md:w-2/3 lg:w-2/3">
                <Card className="bg-surface-page text-text-primary rounded-lg shadow-md">
                  <CardContent className="p-0">
                    <details className="group">
                      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-4 marker:hidden">
                        <h3 className="text-lead font-semibold text-text-primary">
                          {faq.question}
                        </h3>
                        <ChevronDown className="h-6 w-6 shrink-0 text-text-secondary transition-transform duration-300 group-open:rotate-180" />
                      </summary>
                      <div className="px-6 pb-6 pt-2">
                        <p className="text-text-secondary text-lead">{faq.answer}</p>
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
