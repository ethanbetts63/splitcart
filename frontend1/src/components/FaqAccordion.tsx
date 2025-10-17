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
        <AccordionTrigger>How much should I expect to save?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            Savings can vary greatly depending on the items in your cart and the stores you've selected. Our optimization aims to find the maximum possible savings, and we often see users save between 15-30% on their grocery bill.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>What’s a “substitute” and why does it matter?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            A substitute is a similar product that you're willing to buy if your original choice isn't available or is more expensive. For example, a different brand of the same type of milk. Including substitutes gives our algorithm more options to find you the best possible price, potentially increasing your savings.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Is it always cheaper than buying from one store?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            Splitting your cart is often cheaper, but not always. Our results will always show you the "Best Single Store" option alongside the split-cart options, so you can clearly see if splitting your cart provides a real benefit for your specific shopping list.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-4">
        <AccordionTrigger>Which stores can I compare?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            Currently, SplitCart supports major Australian supermarkets including Coles, Woolworths, and Aldi. We are always working to add more stores to our comparison list.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-5">
        <AccordionTrigger>How accurate are the prices?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            We strive to provide the most accurate and up-to-date pricing information by regularly scraping data directly from store websites. However, prices can change rapidly, so there may occasionally be small discrepancies. The final price will always be what you see at the checkout in-store.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-6">
        <AccordionTrigger>Can I choose which stores I want to include or exclude?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            Yes! On the store selection page, you can choose exactly which local stores you're willing to shop at. The cart optimization will only consider the stores you have selected.
          </p>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}