import React, { useState } from 'react';
import { Container, Form, FormControl, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom'; // Import useNavigate
import splitCartTitle from '../assets/splitcart_title_v2.png';

const SearchHeader = ({ setSearchTerm }) => {
  const [inputValue, setInputValue] = useState('');
  const navigate = useNavigate(); // Get the navigate function

  const handleSubmit = (e) => {
    e.preventDefault();
    setSearchTerm(inputValue);
  };

  const handleHomeClick = () => {
    setSearchTerm('');
    setInputValue('');
    navigate('/');
  };

  return (
    <div className="text-center my-5 pt-5">
      <div onClick={handleHomeClick} style={{ cursor: 'pointer' }}> {/* Use onClick */}
        <img src={splitCartTitle} alt="SplitCart" style={{ maxWidth: '375px', marginBottom: '2rem' }} />
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
