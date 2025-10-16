import React, { useEffect } from 'react';
import { useSubstitutions } from '@/context/SubstitutionContext';
import { useStoreSelection } from '@/context/StoreContext';
import ProductTile from '@/components/ProductTile';
import TrolleyItemTile from '@/components/TrolleyItemTile';
import { Button } from '@/components/ui/button';

import { Badge } from '@/components/ui/badge';
import { BadgeCheckIcon } from 'lucide-react';

const SubstitutionPage = () => {
  const {
    itemsToReview,
    substitutes,
    selections,
    fetchSubstitutes,
    updateSelections,
    updateSelectionQuantity,
    currentItemIndex,
    setCurrentItemIndex,
  } = useSubstitutions();
  const { selectedStoreIds } = useStoreSelection();

  const currentItem = itemsToReview[currentItemIndex];
  const currentSubstitutes = substitutes[currentItem?.id] || [];

  useEffect(() => {
    if (currentItem) {
      fetchSubstitutes(currentItem, Array.from(selectedStoreIds));
    }
  }, [currentItem, selectedStoreIds, fetchSubstitutes]);

  const handleNext = () => {
    if (currentItemIndex < itemsToReview.length - 1) {
      setCurrentItemIndex(currentItemIndex + 1);
    }
  };

  const handleBack = () => {
    if (currentItemIndex > 0) {
      setCurrentItemIndex(currentItemIndex - 1);
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

  const handleQuantityChange = (product: Product, quantity: number) => {
    updateSelectionQuantity(currentItem.id, product.id, quantity);
  };

  if (!currentItem) {
    return <div>Loading...</div>; // Or a more sophisticated loading state
  }

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-3 items-center mb-4">
        <div className="justify-self-start">
          <Button onClick={handleBack} disabled={currentItemIndex === 0}>Back</Button>
        </div>
        <h1 className="text-2xl font-bold justify-self-center">Product Substitution</h1>
        <div className="justify-self-end">
          <Button onClick={handleNext} disabled={currentItemIndex === itemsToReview.length - 1}>Next</Button>
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
                />
              )
            })}
          </div>
        </div>
      </div>

    </div>
  );
};

export default SubstitutionPage;