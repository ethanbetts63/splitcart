
import React from 'react';

import aldiLogo from '../assets/ALDI_logo.svg';
import colesLogo from '../assets/coles_logo.webp';
import igaLogo from '../assets/iga_logo.webp';
import woolworthsLogo from '../assets/woolworths_logo.webp';

const companyLogos = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

const CheckableStoreList = ({ stores, selectedStoreIds, onStoreSelect }) => {
    return (
        <div>
            {stores.map(store => {
                const isSelected = selectedStoreIds.has(store.id);
                const style = {
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-light)',
                    padding: '1rem',
                    marginBottom: '0.5rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    boxShadow: isSelected ? '0 0 10px var(--primary)' : 'none',
                    transition: 'boxShadow 0.2s'
                };

                return (
                    <div key={store.id} onClick={() => onStoreSelect(store.id)} style={style}>
                        <div style={{
                            width: '20px',
                            height: '20px',
                            borderRadius: '4px',
                            marginRight: '1rem',
                            backgroundColor: isSelected ? 'var(--primary)' : 'var(--border-muted)', // Changed to use a background color for unselected
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            flexShrink: 0,
                            transition: 'background-color 0.2s'
                        }}>
                            {isSelected && '✔'}
                        </div>
                        <img src={companyLogos[store.company_name]} alt={`${store.company_name} logo`} height="20" style={{ marginRight: '0.5rem' }} />
                        <span style={{ fontFamily: 'Vollkorn', color: 'var(--text)' }}>{store.store_name}</span>
                    </div>
                );
            })}
        </div>
    );
};

export default CheckableStoreList;
