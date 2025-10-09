import React from 'react';
import '../css/LogoButton.css';
import logoSymbol from '../assets/splicart_symbol_v6.png';

const LogoButton = ({ onClick, fontSize }) => {
  const style = {
    fontSize: fontSize || '100px', // Default font size
  };

  return (
    <div onClick={onClick} className="logo-button-container">
      <img src={logoSymbol} alt="SplitCart logo" className="logo-symbol" />
      <h1 className="logo-button-text" style={style}>
        <span className="logo-rest-of-word">SplitCart</span>
      </h1>
    </div>
  );
};

export default LogoButton;