import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubstitutions } from '@/context/SubstitutionContext';
import ProductTile from '@/components/ProductTile';
import TrolleyItemTile from '@/components/TrolleyItemTile';
import { Button } from '@/components/ui/button';
import type { Product } from '@/types/Product';

import { Badge } from '@/components/ui/badge';
import { BadgeCheckIcon } from 'lucide-react';
import { FaqAccordion } from '@/components/FaqAccordion';
import { AspectRatio } from "@/components/ui/aspect-ratio";
import kingKongImage from "../assets/king_kong.png";

const SubstitutionPage = () => {
  const navigate = useNavigate();
  const {
    itemsToReview,
    substitutes,
    selections,
    updateSelections,
    updateSelectionQuantity,
    currentItemIndex,
    setCurrentItemIndex,
  } = useSubstitutions();

  const currentItem = itemsToReview[currentItemIndex];
  const currentSubstitutes = substitutes[currentItem?.id] || [];

  const handleNext = () => {
    if (currentItemIndex < itemsToReview.length - 1) {
      setCurrentItemIndex(currentItemIndex + 1);
    } else {
      navigate('/final-cart');
    }
  };

  const handleBack = () => {
    if (currentItemIndex > 0) {
      setCurrentItemIndex(currentItemIndex - 1);
    } else {
      navigate('/');
    }
  };

  const handleApprove = (product: Product) => {
    const currentSelections = selections[currentItem.id] || [];
    const isAlreadySelected = currentSelections.some(s => s.product.id === product.id);

    let newSelections;
    if (isAlreadySelected) {
      newSelections = currentSelections.filter(s => s.product.id !== product.id).map(s => s.product);
    } else {
      newSelections = [...currentSelections.map(s => s.product), product];
    }
    updateSelections(currentItem.id, newSelections);
  };

  const handleApproveAll = () => {
    if (currentItem && currentSubstitutes.length > 0) {
      updateSelections(currentItem.id, currentSubstitutes);
    }
    handleNext();
  };

  const handleQuantityChange = (product: Product, quantity: number) => {
    updateSelectionQuantity(currentItem.id, product.id, quantity);
  };

  const handleSkipAll = () => {
    navigate('/final-cart');
  };

  if (!currentItem) {
    return <div>Loading...</div>; // Or a more sophisticated loading state
  }

  const isLastItem = currentItemIndex === itemsToReview.length - 1;

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-3 items-center mb-4">
        <div className="justify-self-start flex items-center gap-2">
          <Button onClick={handleBack} className="bg-red-500 text-white">
            {currentItemIndex === 0 ? 'Home' : 'Back'}
          </Button>
          <Button onClick={handleSkipAll} className="bg-black text-white">
            Skip Substitution
          </Button>
        </div>
        <h1 className="text-2xl font-bold justify-self-center">Product Substitution</h1>
        <div className="justify-self-end flex items-center gap-2">
          <Button onClick={handleApproveAll} disabled={currentSubstitutes.length === 0} variant="outline" className="bg-green-500 text-white">
            Approve All
          </Button>
          <Button onClick={handleNext} className="bg-blue-500 text-white">
            {isLastItem ? 'Split my Cart!' : 'Next'}
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-semibold mb-4">Original Product</h2>
          <div className="w-[240px] mx-auto relative">
            <Badge variant="secondary" className="absolute top-2 left-2 z-10 bg-green-500 text-white dark:bg-green-600">
              <BadgeCheckIcon className="w-4 h-4 mr-1" />
              Original Product
            </Badge>
            <ProductTile product={currentItem} />
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-4">Substitutes</h2>
          <div className="h-[480px] overflow-y-auto border rounded-md p-4 space-y-4">
            {currentSubstitutes.map(sub => {
              const selection = (selections[currentItem.id] || []).find(s => s.product.id === sub.id);
              return (
                <TrolleyItemTile 
                  key={sub.id} 
                  product={sub} 
                  onApprove={handleApprove} 
                  isApproved={!!selection}
                  quantity={selection ? selection.quantity : 1}
                  onQuantityChange={handleQuantityChange}
                  context="substitution"
                />
              )
            })}
          </div>
        </div>
      </div>
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <section>
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-4 text-center">Why substitution?</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              <div>
                <FaqAccordion page="substitutes" />
              </div>
              <div>
                <AspectRatio ratio={16 / 9}>
                  <img src={kingKongImage} alt="King Kong swatting at discount planes" className="rounded-md object-contain w-full h-full" />
                </AspectRatio>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default SubstitutionPage;