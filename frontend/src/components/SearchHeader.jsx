import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import searchIcon from '../assets/search.svg';
import LogoButton from './LogoButton';

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
      <div style={{ marginBottom: '2rem' }}>
        <LogoButton onClick={handleHomeClick} fontSize="100px" />
      </div>
      <div style={{ maxWidth: '750px', margin: '0 auto' }}>
        <form style={{ display: 'flex', position: 'relative' }} onSubmit={handleSubmit}>
          <input
            type="search"
            placeholder="Search for products..."
            aria-label="Search"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            style={{ 
              flex: 1, 
              padding: '0.75rem 2.5rem 0.75rem 0.75rem', 
              marginRight: '0.5rem', 
              borderRadius: '15px', 
              marginTop: '5px', 
              border: 'none' 
            }}
          />
          <img 
            src={searchIcon} 
            alt="Search" 
            style={{ 
              position: 'absolute', 
              right: '1rem', 
              top: '50%', 
              transform: 'translateY(-50%)', 
              height: '24px',
              cursor: 'pointer'
            }} 
            onClick={handleSubmit} 
          />
        </form>
      </div>
    </div>
  );
};

export default SearchHeader;