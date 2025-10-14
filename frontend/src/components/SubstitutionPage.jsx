import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useShoppingList } from '../context/ShoppingListContext';
import SubstitutesSection from '../components/SubstitutesSection';
import NextButton from '../components/NextButton';

const SubstitutionPage = () => {
  const { items, substitutes, selections, updateSubstitutionChoices, nearbyStoreIds, removeItem } = useShoppingList();
  const { state } = useLocation();
  const { itemsToReview } = state || { itemsToReview: [] }; // Get itemsToReview from route state
  const navigate = useNavigate();
  const [currentProductIndex, setCurrentProductIndex] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState([]);
  const [productQuantities, setProductQuantities] = useState({});

  const currentItem = itemsToReview[currentProductIndex]; // Use itemsToReview
  const currentSubstitutes = currentItem ? substitutes[currentItem.product.id] : undefined;
  const isLastProduct = currentProductIndex === itemsToReview.length - 1; // Use itemsToReview.length

  const handleNextProduct = () => {
    if (!currentItem) return;

    const allAvailableProducts = [currentItem.product, ...(currentSubstitutes || [])];
    const selectedProducts = allAvailableProducts.filter(p => selectedOptions.includes(p.id));

    if (selectedProducts.length === 0) {
      removeItem(currentItem.product.id);
    } else {
      const selectedProductsWithQuantities = selectedProducts.map(p => ({
          ...p,
          quantity: productQuantities[p.id] || 1
      }));
      updateSubstitutionChoices(currentItem.product.id, selectedProductsWithQuantities);
    }
    setCurrentProductIndex(prev => prev + 1);
  };

  const handleFinishAndSplit = () => {
    if (!currentItem) return;

    const allAvailableProducts = [currentItem.product, ...(currentSubstitutes || [])];
    const selectedProducts = allAvailableProducts.filter(p => selectedOptions.includes(p.id));

    if (selectedProducts.length === 0) {
      removeItem(currentItem.product.id);
      // After removing, we need to construct the cart without this item.
      // The `selections` object will not have an entry for this item if it was just removed.
    } else {
      const selectedProductsWithQuantities = selectedProducts.map(p => ({
          ...p,
          quantity: productQuantities[p.id] || 1
      }));
      const finalSelections = { ...selections, [currentItem.product.id]: selectedProductsWithQuantities };

      // Build formattedCart using the FULL items list from context, applying finalSelections
      const formattedCart = items.map(originalCartItem => {
        if (originalCartItem.product.id === currentItem.product.id && selectedProducts.length === 0) {
          return []; // Don't include this item in the cart
        }
        const originalProductId = originalCartItem.product.id;
        const prods = finalSelections[originalProductId];
        if (prods && prods.length > 0) {
          return prods.map(p => ({ product_id: p.id, quantity: p.quantity }));
        }
        return [{ product_id: originalProductId, quantity: originalCartItem.quantity || 1 }];
      });

      const storeIds = nearbyStoreIds.map(store => store.id);
      navigate('/final-cart', { state: { cart: formattedCart, store_ids: storeIds, original_items: items } });
    }
  };

  // Effect to auto-advance if no substitutes are available for the current item
  useEffect(() => {
    if (currentItem && currentSubstitutes && currentSubstitutes.length === 0) {
      if (isLastProduct) {
        handleFinishAndSplit();
      } else {
        handleNextProduct();
      }
    }
  }, [currentItem, currentSubstitutes, isLastProduct, handleNextProduct, handleFinishAndSplit]);

  // Effect to initialize selected options and quantities when the product changes
  useEffect(() => {
    if (currentItem) {
      const initialQuantities = {};
      initialQuantities[currentItem.product.id] = currentItem.quantity;
      if (currentSubstitutes) {
          currentSubstitutes.forEach(sub => {
              initialQuantities[sub.id] = 1; // Default quantity for substitutes
          });
      }
      setProductQuantities(initialQuantities);
      setSelectedOptions([currentItem.product.id]);
    }
  }, [currentItem, currentSubstitutes]);


  const handleSelectOption = (productId) => {
    setSelectedOptions(prevSelected => {
      return prevSelected.includes(productId)
        ? prevSelected.filter(id => id !== productId)
        : [...prevSelected, productId];
    });
  };

  const handleQuantityChange = (productId, newQuantity) => {
    setProductQuantities(prev => ({ ...prev, [productId]: newQuantity }));
  };

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [currentProductIndex]);

  const handleGoBack = () => {
    setCurrentProductIndex(prev => Math.max(0, prev - 1));
  };

  const handleSkipSubstitution = () => {
    const formattedCart = items.map(item => ([{ product_id: item.product.id, quantity: item.quantity || 1 }]));
    const storeIds = nearbyStoreIds.map(store => store.id);
    navigate('/final-cart', { state: { cart: formattedCart, store_ids: storeIds, original_items: items } });
  };

  const handleApproveAllAndNext = () => {
    if (!currentItem) return;

    const allAvailableProducts = [currentItem.product, ...(currentSubstitutes || [])];
    const selectedProducts = allAvailableProducts; // Approve all
    const selectedProductsWithQuantities = selectedProducts.map(p => ({
        ...p,
        quantity: productQuantities[p.id] || 1
    }));

    if (isLastProduct) {
        const finalSelections = { ...selections, [currentItem.product.id]: selectedProductsWithQuantities };
        const formattedCart = items.map(originalCartItem => {
            const originalProductId = originalCartItem.product.id;
            const prods = finalSelections[originalProductId];
            if (prods && prods.length > 0) {
                return prods.map(p => ({ product_id: p.id, quantity: p.quantity }));
            }
            return [{ product_id: originalProductId, quantity: originalCartItem.quantity || 1 }];
        });
        const storeIds = nearbyStoreIds.map(store => store.id);
        navigate('/final-cart', { state: { cart: formattedCart, store_ids: storeIds, original_items: items } });
    } else {
        updateSubstitutionChoices(currentItem.product.id, selectedProductsWithQuantities);
        setCurrentProductIndex(prev => prev + 1);
    }
  };

  // Show loading spinner if substitutes for the current item are not yet fetched
  if (currentSubstitutes === undefined) {
    return <div style={{ textAlign: 'center', margin: '2rem 0' }}>Loading...</div>;
  }

  return (
    <div style={{ position: 'relative', marginTop: '-4rem' }}>
      {currentProductIndex > 0 && (
        <button onClick={handleGoBack} style={{ position: 'absolute', top: 0, left: 0, zIndex: 1 }} className="btn">Back</button>
      )}
      <div style={{ position: 'absolute', top: 0, right: 0, zIndex: 1, display: 'flex', gap: '0.5rem' }}>
        <button onClick={handleSkipSubstitution} className="btn red-btn">Skip Substitution</button>
        <button onClick={handleApproveAllAndNext} className="btn green-btn">Approve All</button>
      </div>
      <h2 style={{ marginBottom: '-1.5rem', fontSize: '2.5rem' }}>Product Substitution</h2>

      <SubstitutesSection 
        products={[{ ...currentItem.product, is_original: true }, ...(currentSubstitutes || [])]}
        selectedOptions={selectedOptions}
        onSelectOption={handleSelectOption}
        onQuantityChange={handleQuantityChange}
        productQuantities={productQuantities}
      />

      <div style={{ position: 'fixed', bottom: '3rem', right: '3rem', zIndex: 1040 }}>
        <NextButton 
          onClick={isLastProduct ? handleFinishAndSplit : handleNextProduct}
          text={isLastProduct ? 'Split My Cart!' : 'Next Product'}
        />
      </div>
    </div>
  );
};

export default SubstitutionPage;
