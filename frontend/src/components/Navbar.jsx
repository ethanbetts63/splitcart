import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../css/Navbar.css';
import LogoButton from './LogoButton';
import SearchBar from './SearchBar';
import MapButton from './MapButton';
import TrolleyButton from './TrolleyButton';
import logo from '../assets/trolley_v3.png';

const Navbar = ({ searchTerm, setSearchTerm, onShowTrolley, onShowMap }) => {
  const navigate = useNavigate();

  const handleHomeClick = () => {
    if (setSearchTerm) {
      setSearchTerm('');
    }
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="navbar-left" onClick={handleHomeClick}>
        <img src={logo} alt="SplitCart Logo" className="navbar-logo" />
        <LogoButton onClick={handleHomeClick} fontSize="30px" />
      </div>
      <div className="navbar-center">
        <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
      </div>
      <div className="navbar-right">
        <MapButton onClick={onShowMap} />
        <TrolleyButton onClick={onShowTrolley} />
      </div>
    </nav>
  );
};

export default Navbar;
