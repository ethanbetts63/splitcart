import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

export function FaqAccordion() {
  return (
    <Accordion
      type="single"
      collapsible
      className="w-full"
    >
      <AccordionItem value="item-1">
        <AccordionTrigger>How does SplitCart save me money?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            SplitCart compares the price of each item in your shopping list across the stores you select. It then calculates the cheapest combination of stores to buy those items from, splitting your list to maximize your savings.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>Which stores can I compare?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            Currently, SplitCart supports major Australian supermarkets including Coles, Woolworths, and Aldi. We are always working to add more stores to our comparison list.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Is the pricing data accurate?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            We strive to provide the most accurate and up-to-date pricing information by regularly scraping data directly from store websites. However, prices can change rapidly, so there may occasionally be small discrepancies. The final price will always be what you see at the checkout in-store.
          </p>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}
