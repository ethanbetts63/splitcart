'use client';

import { useState } from 'react';
import { useCart } from '../context/CartContext';
import { Switch } from '../components/common/switch';
import { Label } from '../components/common/label';
import ResultsDisplay from '../components/ResultsDisplay';
import { FaqSection } from '../components/FaqSection';

const finalCartFaqs = [
  {
    question: 'How is baseline cost calculated?',
    answer:
      'By taking each item in your list, finding the average price across all available stores, and then summing up these average prices for all items. We use this method, not because it shows the highest savings, but because we believe it is realistic, transparent and honest.',
  },
  {
    question: 'What is the "Best Single Company" option?',
    answer:
      'The cheapest total price if you bought everything from just one company. We find the single company that has the most items on your list for the lowest price, giving you a clear benchmark for your savings.',
  },
  {
    question: 'How can I maximize my savings with SplitCart?',
    answer:
      'Approve more substitutes and/or approve more stores. For example, consider adding stores near your work or on your way home not just close to home.',
  },
];

const FinalCartPage = () => {
  const { optimizationResult, currentCart } = useCart();

  const [viewWithSubstitutes, setViewWithSubstitutes] = useState(true);

  if (!optimizationResult)
    return (
      <div className="site-shell py-4">
        No optimization data available. Please go through the substitution process.
      </div>
    );

  const resultsToShow = viewWithSubstitutes
    ? optimizationResult
    : optimizationResult.no_subs_results;

  return (
    <div className="site-shell py-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-title font-bold text-text-primary">Your Optimised Cart</h1>
          <p className="text-text-muted mt-1">Here&apos;s the cheapest way to buy your list.</p>
        </div>
        {optimizationResult.no_subs_results && (
          <div className="flex items-center gap-3 bg-surface-muted border border-border-default rounded-xl px-4 py-3 self-start sm:self-auto">
            <Switch
              id="substitutes-switch"
              checked={viewWithSubstitutes}
              onCheckedChange={setViewWithSubstitutes}
              className={viewWithSubstitutes ? 'data-[state=checked]:bg-fill-success' : ''}
            />
            <Label htmlFor="substitutes-switch" className="font-medium cursor-pointer select-none">
              Include Substitutes
            </Label>
          </div>
        )}
      </div>

      {resultsToShow && currentCart ? (
        <ResultsDisplay cart={currentCart} data={resultsToShow} />
      ) : (
        <p className="text-text-muted">No results to display for this option.</p>
      )}

      <div className="mt-16">
        <FaqSection title="Helpful Information" faqData={finalCartFaqs} />
      </div>
    </div>
  );
};

export default FinalCartPage;
