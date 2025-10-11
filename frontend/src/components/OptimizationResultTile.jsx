
import React from 'react';
import DisplayOnlyProductTile from './DisplayOnlyProductTile';

const OptimizationResultTile = ({ result, baselineCost, cart }) => {
    const savingsPercentage = baselineCost > 0 ? (result.savings / baselineCost) * 100 : 0;

    return (
        <div style={{ border: '1px solid var(--border)', borderRadius: '8px', marginBottom: '1rem' }}>
            <div style={{ padding: '1rem', paddingTop: 0 }}>
                {Object.entries(result.shopping_plan).map(([storeName, items]) => (
                    items.length > 0 && (
                        <div key={storeName} style={{ marginBottom: '1.5rem' }}>
                            <h6 style={{ fontWeight: 'bold' }}>{storeName}</h6>
                            <div>
                                {items.map((item, itemIndex) => {
                                    const cartItem = cart.find(ci => ci.product && ci.product.name === item.product_name);
                                    const displayItem = {
                                        name: item.product_name,
                                        brand: item.brand,
                                        size: item.sizes.join(', '),
                                        price: item.price,
                                        quantity: cartItem ? cartItem.quantity : 1, // Default to 1 if not found
                                        image_url: cartItem ? cartItem.product.image_url : '' // Default to empty if not found
                                    };

                                    return <DisplayOnlyProductTile key={itemIndex} item={displayItem} />;
                                })}
                            </div>
                        </div>
                    )
                ))}
            </div>
        </div>
    );
};

export default OptimizationResultTile;
