import React, { useState, useEffect } from 'react';
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
    <div style={{ textAlign: 'center', margin: '3rem 0' }}>
      <div onClick={handleHomeClick} style={{ cursor: 'pointer' }}>
        <h1 style={{ fontFamily: 'Vollkorn', fontStyle: 'italic', fontSize: '100px', color: 'var(--primary)', marginBottom: '2rem' }}>
          splitcart
        </h1>
      </div>
      <div style={{ maxWidth: '750px', margin: '0 auto' }}>
        <form style={{ display: 'flex' }} onSubmit={handleSubmit}>
          <input
            type="search"
            placeholder="Search for products..."
            aria-label="Search"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            style={{ flex: 1, padding: '0.75rem', marginRight: '0.5rem' }}
          />
          <button style={{ backgroundColor: 'var(--primary)', color: 'white' }} type="submit">Search</button>
        </form>
      </div>
    </div>
  );
};

export default SearchHeader;