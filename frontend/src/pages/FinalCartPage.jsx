import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import OptimizationResultTile from '../components/OptimizationResultTile';

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
        return <div className="flex justify-center items-center h-screen"><div>Loading...</div></div>;
    }

    if (error) {
        return <div className="flex justify-center items-center h-screen"><div>Error: {error}</div></div>;
    }

    return (
        <div className="bg-gray-100 min-h-screen">
            <div className="container mx-auto p-4 sm:p-6 lg:p-8">
                <h1 className="text-3xl sm:text-4xl font-bold mb-6 text-gray-800 border-b pb-2">Optimized Shopping Cart</h1>
                {optimizationData && (
                    <div>
                        {optimizationData.optimization_results.map((result, index) => (
                            <OptimizationResultTile 
                                key={index} 
                                result={result} 
                                baselineCost={optimizationData.baseline_cost} 
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default FinalCartPage;