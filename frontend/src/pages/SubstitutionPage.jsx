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

  const currentShoppingListItem = items[currentProductIndex];

  useEffect(() => {
    if (!currentShoppingListItem || !userLocation) return;

    const fetchSubstitutes = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (userLocation && userLocation.postcode && userLocation.radius) {
          params.append('postcode', userLocation.postcode);
          params.append('radius', userLocation.radius);
        }
        
        const response = await fetch(`/api/products/${currentShoppingListItem.product.id}/substitutes/?${params.toString()}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('API Response Data:', data); // DEBUGGING
        setSubstitutes(data);
        setSelectedOptions([currentShoppingListItem.product.id]); // Select original by default

        // If no substitutes found, automatically select original and advance
        if (data.length === 0) {
          updateSubstitutionChoices(currentShoppingListItem.product.id, [currentShoppingListItem.product.id]);
          setCurrentProductIndex(prev => prev + 1);
        }

      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSubstitutes();
  }, [currentShoppingListItem, userLocation, updateSubstitutionChoices]); // Re-fetch when current product or user location changes

  const handleSelectOption = (productId) => {
    setSelectedOptions(prevSelected => {
      if (prevSelected.includes(productId)) {
        return prevSelected.filter(id => id !== productId);
      } else {
        return [...prevSelected, productId];
      }
    });
  };

  const handleNextProduct = () => {
    // Save current selections
    updateSubstitutionChoices(currentShoppingListItem.product.id, selectedOptions);
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

  if (!currentShoppingListItem) {
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
        products={[{ ...currentShoppingListItem.product, is_original: true }, ...substitutes]}
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
