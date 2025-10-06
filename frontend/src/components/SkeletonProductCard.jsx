import React from 'react';
import placeholderImage from '../assets/trolley_v3.png';

const SkeletonProductCard = () => {
  return (
        <div style={{ border: '1px solid var(--border)', borderRadius: '8px', width: '18rem', minWidth: '18rem', marginRight: '1rem', backgroundColor: '#FFFFFF' }}>
      <img
        src={placeholderImage}
        style={{
          opacity: 0.3,
          objectFit: 'contain',
          height: '180px', // Approximate height of real product images
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
  );
};

export default SkeletonProductCard;
