import React, { useState } from 'react';
import { Container, Form, FormControl, Button } from 'react-bootstrap';

const SearchHeader = ({ setSearchTerm }) => {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setSearchTerm(inputValue);
  };

  return (
    <div className="text-center my-5">
      <h1>SplitCart</h1>
      <Container style={{ maxWidth: '600px' }}>
        <Form className="d-flex" onSubmit={handleSubmit}>
          <FormControl
            type="search"
            placeholder="Search for products..."
            className="me-2"
            aria-label="Search"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
          <Button variant="outline-success" type="submit">Search</Button>
        </Form>
      </Container>
    </div>
  );
};

export default SearchHeader;
