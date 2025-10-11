import React from 'react';
import DisplayOnlyProductTile from './DisplayOnlyProductTile';

const StoreListComponent = ({ storeName, items, cart }) => {
    const style = {
        background: '#fff',
        padding: '1rem',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    };

    return (
        <div style={style}>
            <h6 style={{ fontWeight: 'bold', marginTop: 0 }}>{storeName}</h6>
            <div>
                {items.map((item, itemIndex) => {
                    const cartItem = cart.find(ci => ci.product && ci.product.name === item.product_name);
                    const displayItem = {
                        name: item.product_name,
                        brand: item.brand,
                        size: item.sizes.join(', '),
                        price: item.price,
                        quantity: cartItem ? cartItem.quantity : 1,
                        image_url: cartItem ? cartItem.product.image_url : ''
                    };

                    return <DisplayOnlyProductTile key={itemIndex} item={displayItem} />;
                })}
            </div>
        </div>
    );
};

export default StoreListComponent;
