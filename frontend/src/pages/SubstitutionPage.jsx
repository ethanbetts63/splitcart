import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useShoppingList } from '../context/ShoppingListContext';
import SubstitutesSection from '../components/SubstitutesSection';
import LocationSetupModal from '../components/LocationSetupModal'; // To get userLocation

const SubstitutionPage = () => {
  const { items, substitutes, selections, updateSubstitutionChoices, nearbyStoreIds } = useShoppingList();
  const { state } = useLocation();
  const { itemsToReview } = state || { itemsToReview: [] }; // Get itemsToReview from route state
  const navigate = useNavigate();
  const [currentProductIndex, setCurrentProductIndex] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState([]);

  const currentItem = itemsToReview[currentProductIndex]; // Use itemsToReview
  const currentSubstitutes = currentItem ? substitutes[currentItem.product.id] : undefined;
  const isLastProduct = currentProductIndex === itemsToReview.length - 1; // Use itemsToReview.length

  const handleNextProduct = () => {
    if (!currentItem) return;

    const allAvailableProducts = [currentItem.product, ...(currentSubstitutes || [])];
    const selectedProducts = allAvailableProducts.filter(p => selectedOptions.includes(p.id));
    
    updateSubstitutionChoices(currentItem.product.id, selectedProducts);
    setCurrentProductIndex(prev => prev + 1);
  };

  const handleFinishAndSplit = () => {
    if (!currentItem) return;

    const allAvailableProducts = [currentItem.product, ...(currentSubstitutes || [])];
    const selectedProducts = allAvailableProducts.filter(p => selectedOptions.includes(p.id));
    
    const finalSelections = { ...selections, [currentItem.product.id]: selectedProducts };

    // Build formattedCart using the FULL items list from context, applying finalSelections
    const formattedCart = items.map(originalCartItem => {
      const originalProductId = originalCartItem.product.id;
      const prods = finalSelections[originalProductId];
      if (prods && prods.length > 0) {
        return prods.map(p => ({ product_id: p.id, quantity: originalCartItem.quantity }));
      }
      return [{ product_id: originalProductId, quantity: originalCartItem.quantity || 1 }];
    });

    navigate('/final-cart', { state: { cart: formattedCart, store_ids: nearbyStoreIds } });
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

  // Effect to initialize selected options when the product changes
  useEffect(() => {
    if (currentItem) {
      setSelectedOptions([currentItem.product.id]);
    }
  }, [currentItem]);


  const handleSelectOption = (productId) => {
    setSelectedOptions(prevSelected => {
      if (productId === currentItem.product.id) return prevSelected; // Prevent deselecting original
      return prevSelected.includes(productId)
        ? prevSelected.filter(id => id !== productId)
        : [...prevSelected, productId];
    });
  };

  // Show loading spinner if substitutes for the current item are not yet fetched
  if (currentSubstitutes === undefined) {
    return <div style={{ textAlign: 'center', margin: '2rem 0' }}>Loading...</div>;
  }

  return (
    <div style={{ marginTop: '2rem' }}>
      <h2>Product Substitution</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
        Reviewing substitutes for: <strong>{currentItem.product.name}</strong>
      </p>

      <SubstitutesSection 
        products={[{ ...currentItem.product, is_original: true }, ...(currentSubstitutes || [])]}
        selectedOptions={selectedOptions}
        onSelectOption={handleSelectOption}
      />

      <button
        onClick={isLastProduct ? handleFinishAndSplit : handleNextProduct}
        style={{ marginTop: '1.5rem', backgroundColor: 'var(--primary)', color: 'white' }}
      >
        {isLastProduct ? 'Split My Cart' : 'Next Product'}
      </button>
    </div>
  );
};export default SubstitutionPage;
