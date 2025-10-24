import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '@/context/CartContext';
import { useStoreList } from '@/context/StoreListContext';
import ProductTile from '@/components/ProductTile';
import CartItemTile from '@/components/CartItemTile';
import { Button } from '@/components/ui/button';
import type { Product, CartItem } from '@/types';

import { Badge } from "@/components/ui/badge";
import { BadgeCheckIcon } from 'lucide-react';
import { FaqAccordion } from '@/components/FaqAccordion';
import { FaqImageSection } from "../components/FaqImageSection";
import kingKongImage from "../assets/king_kong.png";

const SubstitutionPage = () => {
  const navigate = useNavigate();
  const { currentCart, potentialSubstitutes, setOptimizationResult } = useCart();
  const { selectedStoreIds } = useStoreList();

  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [approvedSelections, setApprovedSelections] = useState<{ [originalItemId: string]: { product: Product, quantity: number }[] }>({});

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const itemsToReview = currentCart?.items.filter(item => potentialSubstitutes[item.product.id]?.length > 0) || [];
  const currentItem = itemsToReview[currentItemIndex];
  const currentSubstitutes = currentItem ? potentialSubstitutes[currentItem.product.id] : [];

  const handleNext = () => {
    if (currentItemIndex < itemsToReview.length - 1) {
      setCurrentItemIndex(currentItemIndex + 1);
    } else {
      handleOptimizeAndNavigate();
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
    const currentSelections = approvedSelections[currentItem.id] || [];
    const isAlreadySelected = currentSelections.some(s => s.product.id === product.id);

    let newSelections;
    if (isAlreadySelected) {
      newSelections = currentSelections.filter(s => s.product.id !== product.id);
    } else {
      newSelections = [...currentSelections, { product, quantity: 1 }];
    }
    setApprovedSelections(prev => ({ ...prev, [currentItem.id]: newSelections }));
  };

  const handleQuantityChange = (product: Product, quantity: number) => {
    const currentSelections = approvedSelections[currentItem.id] || [];
    const newSelections = currentSelections.map(s => s.product.id === product.id ? { ...s, quantity } : s);
    setApprovedSelections(prev => ({ ...prev, [currentItem.id]: newSelections }));
  };

  const handleOptimizeAndNavigate = async () => {
    if (!currentCart) return;

    const cartPayload = currentCart.items.map(item => {
      const approved = approvedSelections[item.id] || [];
      const slot = [{ product_id: item.product.id, quantity: item.quantity }];
      approved.forEach(sel => {
        slot.push({ product_id: sel.product.id, quantity: sel.quantity });
      });
      return slot;
    });

    const originalItemsPayload = currentCart.items.map(item => ({
      product: { id: item.product.id },
      quantity: item.quantity
    }));

    const optimizationData = {
      cart: cartPayload,
      store_ids: Array.from(selectedStoreIds),
      original_items: originalItemsPayload,
    };

    try {
      const response = await fetch('/api/cart/split/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(optimizationData),
      });
      if (!response.ok) throw new Error('Optimization failed');
      const results = await response.json();
      setOptimizationResult(results);
      navigate('/final-cart');
    } catch (error) {
      console.error(error);
    }
  };

  if (!currentItem) {
    return (
      <div className="text-center p-8">
        <h2 className="text-2xl font-bold mb-4">No Substitutes to Review</h2>
        <p className="mb-4">None of the items in your cart currently have substitute options available.</p>
        <Button onClick={handleOptimizeAndNavigate}>Proceed to Final Cart</Button>
      </div>
    );
  }

  const isLastItem = currentItemIndex === itemsToReview.length - 1;

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-3 items-center mb-4">
        <div className="justify-self-start flex items-center gap-2">
          <Button onClick={handleBack} className="bg-red-500 text-white">
            {currentItemIndex === 0 ? 'Home' : 'Back'}
          </Button>
        </div>
        <h1 className="text-2xl font-bold justify-self-center">Product Substitution</h1>
        <div className="justify-self-end flex items-center gap-2">
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
            <ProductTile product={currentItem.product} />
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-4">Substitutes</h2>
          <div className="h-[480px] overflow-y-auto border rounded-md p-4 space-y-4">
            {currentSubstitutes.map(sub => {
              const selection = (approvedSelections[currentItem.id] || []).find(s => s.product.id === sub.id);
              return (
                <CartItemTile 
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
            <FaqImageSection
              title="Why substitution?"
              page="substitutes"
              imageSrc={kingKongImage}
              imageAlt="King Kong swatting at discount planes"
            />
          </section>
        </div>
      </div>
    </div>
  );
};

export default SubstitutionPage;