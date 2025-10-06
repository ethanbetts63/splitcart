
import React from 'react';

const OptimizationResultTile = ({ result, baselineCost }) => {
    return (
        <details style={{ border: '1px solid var(--border)', borderRadius: '8px', marginBottom: '1rem' }}>
            <summary style={{ padding: '1rem', cursor: 'pointer' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <div>
                        <h5>{result.max_stores} Store Option</h5>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <p>Optimized Cost: <span style={{ fontWeight: 'bold', color: 'var(--primary)' }}>${result.optimized_cost.toFixed(2)}</span></p>
                        <p>Savings: <span style={{ fontWeight: 'bold', color: 'var(--success)' }}>${result.savings.toFixed(2)}</span></p>
                    </div>
                </div>
            </summary>
            <div style={{ padding: '1rem' }}>
                {Object.entries(result.shopping_plan).map(([storeName, items]) => (
                    items.length > 0 && (
                        <div key={storeName} style={{ marginBottom: '1.5rem' }}>
                            <h6 style={{ fontWeight: 'bold' }}>{storeName}</h6>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr>
                                        <th style={{ border: '1px solid var(--border)', padding: '0.5rem' }}>Product</th>
                                        <th style={{ border: '1px solid var(--border)', padding: '0.5rem' }}>Brand</th>
                                        <th style={{ border: '1px solid var(--border)', padding: '0.5rem' }}>Size</th>
                                        <th style={{ border: '1px solid var(--border)', padding: '0.5rem', textAlign: 'right' }}>Price</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {items.map((item, itemIndex) => (
                                        <tr key={itemIndex}>
                                            <td style={{ border: '1px solid var(--border)', padding: '0.5rem' }}>{item.product_name}</td>
                                            <td style={{ border: '1px solid var(--border)', padding: '0.5rem' }}>{item.brand}</td>
                                            <td style={{ border: '1px solid var(--border)', padding: '0.5rem' }}>{item.sizes.join(', ')}</td>
                                            <td style={{ border: '1px solid var(--border)', padding: '0.5rem', textAlign: 'right' }}>${item.price.toFixed(2)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )
                ))}
            </div>
        </details>
    );
};

export default OptimizationResultTile;
