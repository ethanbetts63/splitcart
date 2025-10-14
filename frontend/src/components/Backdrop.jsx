import React from 'react';
import '../css/Backdrop.css';

const Backdrop = ({ show, onClick }) => {
  return <div className={`backdrop ${show ? 'visible' : ''}`} onClick={onClick}></div>;
};

export default Backdrop;
