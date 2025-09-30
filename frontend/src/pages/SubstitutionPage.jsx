import React, { useState, useEffect } from 'react';
import { Container, Button, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';
import SubstitutesSection from '../components/SubstitutesSection';
import LocationSetupModal from '../components/LocationSetupModal'; // To get userLocation

export const SubstitutionPage = () => {
  const { items, updateSubstitutionChoices } = useShoppingList();
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
    if (!currentShoppingListSlot || !userLocation) return;

    const fetchSubstitutes = async () => {
      setLoading(true);
      setError(null);
      try {
        const primaryItem = currentShoppingListSlot[0];
        const params = new URLSearchParams();
        if (userLocation && userLocation.postcode && userLocation.radius) {
          params.append('postcode', userLocation.postcode);
          params.append('radius', userLocation.radius);
        }
        
        const response = await fetch(`/api/products/${primaryItem.product.id}/substitutes/?${params.toString()}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setSubstitutes(data);
        // Default selection includes only the original product's ID
        setSelectedOptions([primaryItem.product.id]);

        // If no substitutes are found, we can auto-confirm the original and move on.
        if (data.length === 0) {
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
  }, [currentShoppingListSlot, userLocation, updateSubstitutionChoices]); // Re-fetch when current slot or user location changes

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
        {/* TODO: Display summary or navigate to next step */}
        <Button variant="primary">View Final Cart</Button>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <h2>Split My Cart: Product Substitution</h2>
      <p className="text-muted mb-4">
        Please select all items you are willing to consider as substitutes for the original product. 
        The more options you provide, the greater the flexibility the algorithm has to optimize your total cart cost. 
        The system aims for the lowest overall cart price, which might involve selecting a seemingly more expensive 
        individual substitute if it leads to greater savings across your entire shopping list.
      </p>

      <SubstitutesSection 
        products={[{ ...currentShoppingListSlot[0].product, is_original: true }, ...substitutes]}
        selectedOptions={selectedOptions}
        onSelectOption={handleSelectOption}
      />

      <Button
        variant="primary"
        onClick={handleNextProduct}
        className="mt-3"
      >
        Next Product
      </Button>
    </Container>
  );
};

export default SubstitutionPage;
