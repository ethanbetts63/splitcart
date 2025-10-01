import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

const FinalCartPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { cart, store_ids } = location.state || {};

    const [optimizationResult, setOptimizationResult] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!cart || !store_ids) {
            // Redirect back if state is not present
            navigate('/'); // Or to the shopping list page
            return;
        }

        const fetchOptimizedCart = async () => {
            try {
                const response = await axios.post('/api/cart/split/', {
                    cart: cart,
                    store_ids: store_ids,
                });
                setOptimizationResult(response.data);
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
            {optimizationResult && (
                <div>
                    <div className="mb-4">
                        <p><strong>Total Cost:</strong> ${optimizationResult.optimized_cost.toFixed(2)}</p>
                        <p><strong>Baseline Cost:</strong> ${optimizationResult.baseline_cost.toFixed(2)}</p>
                        <p className="text-green-600"><strong>Savings:</strong> ${optimizationResult.savings.toFixed(2)}</p>
                    </div>
                    <div>
                                                {Object.entries(optimizationResult.shopping_plan).map(([storeName, items]) => (
                                                    items.length > 0 && (
                                                        <div key={storeName} className="mb-4 p-4 border rounded">
                                                            <h2 className="text-xl font-semibold">{storeName}</h2>
                                                            <ul>
                                                                {items.map((item, index) => (
                                                                                                                <li key={index} className="flex justify-between">
                                                                                                                    <span>{item.product}</span>
                                                                                                                    <span>${item.price.toFixed(2)}</span>
                                                                                                                </li>                                                                ))}
                                                            </ul>
                                                        </div>
                                                    )
                                                ))}                    </div>
                </div>
            )}
        </div>
    );
};

export default FinalCartPage;
