import React from 'react';

const Footer = () => {
  return (
    <footer className="footer" style={{ padding: '1rem 0', textAlign: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <span>&copy; {new Date().getFullYear()} SplitCart</span>
      </div>
    </footer>
  );
};

export default Footer;