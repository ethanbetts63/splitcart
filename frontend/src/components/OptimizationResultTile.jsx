
import React from 'react';
import StoreListComponent from './StoreListComponent';

const OptimizationResultTile = ({ result, cart }) => {
    return (
        <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                {Object.entries(result.shopping_plan).map(([storeName, items]) => (
                    items.length > 0 && (
                        <StoreListComponent 
                            key={storeName} 
                            storeName={storeName} 
                            items={items} 
                            cart={cart} 
                        />
                    )
                ))}
            </div>
        </div>
    );
};

export default OptimizationResultTile;
