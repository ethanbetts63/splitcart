
import React from 'react';
import StoreListComponent from './StoreListComponent';

const OptimizationResultTile = ({ result, cart }) => {
    return (
        <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1rem' }}>
                {Object.entries(result.shopping_plan).map(([storeName, storeData]) => (
                    storeData.items.length > 0 && (
                        <StoreListComponent 
                            key={storeName} 
                            storeName={storeName} 
                            storeData={storeData} 
                            cart={cart} 
                        />
                    )
                ))}            </div>
        </div>
    );
};

export default OptimizationResultTile;
