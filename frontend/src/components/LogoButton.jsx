import React from 'react';
import '../css/LogoButton.css';

const LogoButton = ({ onClick, fontSize }) => {
  const style = {
    fontSize: fontSize || '100px', // Default font size
  };

  return (
    <div onClick={onClick} className="logo-button-container">
      <h1 className="logo-button-text" style={style}>
        S<span className="logo-rest-of-word">plitCart</span><span className="logo-domain">.com.au</span>
      </h1>
    </div>
  );
};

export default LogoButton;
