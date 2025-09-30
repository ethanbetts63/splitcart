import React, { useState, useEffect } from 'react';
import { Container, Button, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';
import SubstitutesSection from '../components/SubstitutesSection';
import LocationSetupModal from '../components/LocationSetupModal'; // To get userLocation
import { useNavigate } from 'react-router-dom';

export const SubstitutionPage = ({ nearbyStoreIds }) => {
  const { items, updateSubstitutionChoices } = useShoppingList();
  const navigate = useNavigate();
  const [currentProductIndex, setCurrentProductIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [substitutes, setSubstitutes] = useState([]);
  const [userLocation, setUserLocation] = useState(null); // { postcode: 'XXXX', radius: Y }
  const [selectedOptions, setSelectedOptions] = useState([]); // State for current product's selections

  // Load user location from localStorage
  useEffect(() => {
    const savedLocation = localStorage.getItem('userLocation');
    if (savedLocation) {
      setUserLocation(JSON.parse(savedLocation));
    }
  }, []);

  const currentShoppingListSlot = items[currentProductIndex];

  useEffect(() => {
    if (!currentShoppingListSlot || !userLocation || nearbyStoreIds.length === 0) return;

    const primaryItem = currentShoppingListSlot[0];

    // Initialize local state with the product IDs already present in the context for this slot.
    const existingIds = currentShoppingListSlot.map(item => item.product.id);
    setSelectedOptions(existingIds);

    const fetchSubstitutes = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        // Pass store_ids to the substitutes API
        if (nearbyStoreIds && nearbyStoreIds.length > 0) {
          params.append('store_ids', nearbyStoreIds.join(','));
        }
        
        const response = await fetch(`/api/products/${primaryItem.product.id}/substitutes/?${params.toString()}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setSubstitutes(data);

        // Auto-advance if no substitutes are found and the slot only contains the primary item.
        if (data.length === 0 && currentShoppingListSlot.length === 1) {
          updateSubstitutionChoices(primaryItem.product.id, [primaryItem.product]);
          setCurrentProductIndex(prev => prev + 1);
        }

      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSubstitutes();
  }, [currentShoppingListSlot, userLocation, nearbyStoreIds, updateSubstitutionChoices]); // Re-fetch when current slot, user location, or nearbyStoreIds changes

  const handleSelectOption = (productId) => {
    setSelectedOptions(prevSelected => {
      // Prevent deselecting the original product
      if (productId === currentShoppingListSlot[0].product.id) return prevSelected;
      
      if (prevSelected.includes(productId)) {
        return prevSelected.filter(id => id !== productId);
      } else {
        return [...prevSelected, productId];
      }
    });
  };

  const handleNextProduct = () => {
    const primaryItem = currentShoppingListSlot[0];
    // All possible choices for this slot: the original product plus the fetched substitutes.
    const allAvailableProducts = [primaryItem.product, ...substitutes];
    // Filter this list to get the full objects of what the user selected.
    const selectedProducts = allAvailableProducts.filter(p => selectedOptions.includes(p.id));
    
    // Save the full product objects to the context.
    updateSubstitutionChoices(primaryItem.product.id, selectedProducts);
    setCurrentProductIndex(prev => prev + 1);
  };

  const handleViewFinalCart = () => {
    // The cart data needs to be in the format expected by build_price_slots
    // which is a list of lists of product IDs (or objects with product_id and quantity)
    const formattedCart = items.map(slot => 
      slot.map(item => ({ product_id: item.product.id, quantity: item.quantity || 1 }))
    );

    navigate('/final-cart', { state: { cart: formattedCart, store_ids: nearbyStoreIds } });
  };

  if (items.length === 0) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="info">Your shopping list is empty. Add some products to start splitting your cart!</Alert>
        <Button variant="primary" onClick={() => window.history.back()}>Go Back to Shopping</Button>
      </Container>
    );
  }

  if (!currentShoppingListSlot) {
    return (
      <Container fluid className="mt-4">
        <h2>Substitution Complete!</h2>
        <p>You have reviewed all products in your cart.</p>
        <Button variant="primary" onClick={handleViewFinalCart}>View Final Cart</Button>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <h2>Product Substitution</h2>
      <p className="text-muted mb-4">
        Please select all items you are willing to consider as substitutes for the original product. 
        The more options you provide, the greater the flexibility the algorithm has to optimize your total cart cost. 
        The system aims for the lowest overall cart price, which might involve selecting a seemingly more expensive 
        individual substitute if it leads to greater savings across your entire shopping list.
      </p>

      <Button
        variant="primary"
        onClick={handleNextProduct}
        className="mt-3"
      >
        Next Product
      </Button>

      <SubstitutesSection 
        products={[{ ...currentShoppingListSlot[0].product, is_original: true }, ...substitutes]}
        selectedOptions={selectedOptions}
        onSelectOption={handleSelectOption}
      />
    </Container>
  );
};

export default SubstitutionPage;
