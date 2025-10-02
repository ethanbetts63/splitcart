import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

const FinalCartPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { cart, store_ids } = location.state || {};

    const [optimizationData, setOptimizationData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const splitCalledRef = useRef(false); // Flag to prevent double API calls

    useEffect(() => {
        if (!cart || !store_ids) {
            navigate('/');
            return;
        }

        if (splitCalledRef.current) {
            return; // Don't call API if it has already been called
        }
        splitCalledRef.current = true; // Set flag to true immediately

        const fetchOptimizedCart = async () => {
            try {
                const response = await axios.post('/api/cart/split/', {
                    cart: cart,
                    store_ids: store_ids,
                    max_stores_options: [2, 3, 4]
                });
                setOptimizationData(response.data);
            } catch (err) {
                setError(err.response ? err.response.data.error : 'An unexpected error occurred.');
            } finally {
                setLoading(false);
            }
        };

        fetchOptimizedCart();
    }, [cart, store_ids, navigate]);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">Optimized Shopping Cart</h1>
            {optimizationData && (
                <div>
                    <div className="mb-4">
                        <p><strong>Baseline Cost (Single Store):</strong> ${optimizationData.baseline_cost.toFixed(2)}</p>
                    </div>
                    {optimizationData.optimization_results.map((result, index) => (
                        <div key={index} className="mb-8 p-4 border rounded-lg shadow-md">
                            <h2 className="text-2xl font-bold mb-3">Option {index + 1}: {result.max_stores} Stores</h2>
                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <p><strong>Optimized Cost:</strong> ${result.optimized_cost.toFixed(2)}</p>
                                <p className="text-green-600"><strong>Savings:</strong> ${result.savings.toFixed(2)}</p>
                            </div>
                            <div>
                                {Object.entries(result.shopping_plan).map(([storeName, items]) => (
                                    items.length > 0 && (
                                        <div key={storeName} className="mb-4 p-4 border rounded">
                                            <h3 className="text-xl font-semibold">{storeName}</h3>
                                            <ul>
                                                {items.map((item, itemIndex) => (
                                                    <li key={itemIndex} className="flex justify-between">
                                                        <span>{item.product}</span>
                                                        <span>${item.price.toFixed(2)}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default FinalCartPage;
