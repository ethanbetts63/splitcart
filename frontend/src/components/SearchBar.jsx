import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import searchIcon from '../assets/search.svg';
import '../css/SearchBar.css';

const SearchBar = ({ searchTerm, setSearchTerm }) => {
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

  return (
    <form className="search-bar-form" onSubmit={handleSubmit}>
      <input
        type="search"
        placeholder="Search for products..."
        aria-label="Search"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        className="search-bar-input"
      />
      <img
        src={searchIcon}
        alt="Search"
        className="search-bar-icon"
        onClick={handleSubmit}
      />
    </form>
  );
};

export default SearchBar;
