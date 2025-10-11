import React from 'react';
import logoSymbol from '../assets/splitcart_symbol_v6.png';

const SkeletonProductCard = () => {

  const cardStyle = {
    border: '0.1px solid black',
    borderRadius: '8px',
    width: '18rem',
    minWidth: '18rem',
    marginRight: '1rem',
    backgroundColor: '#FFFFFF'
  };

  const mediaQueryStyles = `
    @media (max-width: 768px) {
      .skeleton-card {
        width: 13.5rem !important;
        min-width: 13.5rem !important;
      }
    }
  `;

  return (
    <div>
      <style>{mediaQueryStyles}</style>
      <div className="skeleton-card" style={cardStyle}>
        <img
          src={logoSymbol}
          style={{
            opacity: 0.3,
            objectFit: 'contain',
            height: '180px',
            width: '100%'
          }}
        />
        <div style={{ padding: '1rem' }}>
          <div style={{ height: '1.5rem', backgroundColor: 'var(--highlight)', marginBottom: '0.5rem', width: '80%' }}></div>
          <div style={{ height: '1.25rem', backgroundColor: 'var(--highlight)', marginBottom: '0.5rem', width: '50%' }}></div>
          <div style={{ height: '1rem', backgroundColor: 'var(--highlight)', marginBottom: '1rem', width: '40%' }}></div>
          <div style={{ height: '2.5rem', backgroundColor: 'var(--primary)', width: '60%' }}></div>
        </div>
      </div>
    </div>
  );
};

export default SkeletonProductCard;
