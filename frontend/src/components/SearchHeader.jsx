import React from 'react';
import { Container, Form, FormControl, Button } from 'react-bootstrap';

const SearchHeader = () => {
  return (
    <div className="text-center my-5">
      <h1>SplitCart</h1>
      <Container style={{ maxWidth: '600px' }}>
        <Form className="d-flex">
          <FormControl
            type="search"
            placeholder="Search for products..."
            className="me-2"
            aria-label="Search"
          />
          <Button variant="outline-success">Search</Button>
        </Form>
      </Container>
    </div>
  );
};

export default SearchHeader;
