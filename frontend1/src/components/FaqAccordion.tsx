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
        <AccordionTrigger>Will I really save 15%?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            Hopefully! Our optimization aims to find the maximum possible savings. But it's restricted by the stores you choose, the items in you select and the substitutes you approve. Some shopping lists have more potential for savings than others, so individual results will vary but we find that 15% is a fairly consistant average.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>What’s a “substitute” and why does it matter?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            A substitute is a product you would be willing to have "instead of" the original product you choose. For example, a different brand of the same type of milk. Including substitutes gives our algorithm a lot more options to play with and is major factor in the savings you should expect. We know it's a annoying to do but it's also the reason we can save you more than any other comparison site.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Is it always cheaper than buying from one store?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            Splitting your cart is almost always cheaper, almost. Our results will always show you the "Best Single Store" option alongside the split-cart options, so you can clearly see if splitting your cart provides a real benefit for your specific shopping list.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-4">
        <AccordionTrigger>Which stores can I compare?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            Right now, SplitCart supports Coles, Woolworths, Aldi, and IGA. We’d love to bring the smaller guys on board too, but their price data is harder to track down — which hurts, because they’re often the real discount heroes.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-5">
        <AccordionTrigger>How accurate are the prices?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            The short answer is: pretty accurate! But not perfect. We pull prices directly from stores websites as often as we can but we can only be as accurate as the stores themselves.
          </p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-6">
        <AccordionTrigger>Can I choose which stores I want to include or exclude?</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance">
          <p>
            Yes! There's a little location button in the top right. Click it to open the store selection menu where you can choose which stores to include in your comparison. The more the better!
          </p>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}