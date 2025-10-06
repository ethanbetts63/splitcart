import React, { useState, useEffect } from 'react';
import { Container, Form, FormControl, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const SearchHeader = ({ searchTerm, setSearchTerm }) => {
  const [inputValue, setInputValue] = useState(searchTerm);
  const navigate = useNavigate();

  useEffect(() => {
    setInputValue(searchTerm);
  }, [searchTerm]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSearchTerm(inputValue);
    navigate(`/products?search=${encodeURIComponent(inputValue)}`);
  };

  const handleHomeClick = () => {
    setSearchTerm('');
    setInputValue('');
    navigate('/');
  };

  return (
    <div className="text-center my-5 pt-5">
      <div onClick={handleHomeClick} style={{ cursor: 'pointer' }}>
        <h1 style={{ fontFamily: 'Vollkorn', fontStyle: 'italic', fontSize: '100px', color: 'var(--logo-color)', marginBottom: '2rem' }}>
          splitcart
        </h1>
      </div>
      <Container style={{ maxWidth: '750px' }}>
        <Form className="d-flex" onSubmit={handleSubmit}>
          <FormControl
            type="search"
            placeholder="Search for products..."
            className="me-2"
            aria-label="Search"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            size="lg"
          />
          <Button style={{ backgroundColor: '#1CC3B9', color: 'white' }} type="submit" size="lg">Search</Button>
        </Form>
      </Container>
    </div>
  );
};

export default SearchHeader;