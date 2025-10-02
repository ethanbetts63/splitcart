
import React, { useState } from 'react';

const OptimizationResultTile = ({ result, baselineCost }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <div className="mb-8 p-4 border rounded-lg shadow-md bg-white cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold">{result.max_stores} Store Option</h2>
                    <p className="text-lg">Optimized Cost: <span className="font-semibold text-blue-600">${result.optimized_cost.toFixed(2)}</span></p>
                    <p className="text-lg">Savings: <span className="font-semibold text-green-600">${result.savings.toFixed(2)}</span></p>
                </div>
                <div className="text-right">
                    <p className="text-sm text-gray-500">Baseline Cost: ${baselineCost.toFixed(2)}</p>
                    <button className="text-blue-500 hover:text-blue-700">
                        {isExpanded ? 'Collapse' : 'Expand'}
                    </button>
                </div>
            </div>

            {isExpanded && (
                <div className="mt-4 pt-4 border-t">
                    {Object.entries(result.shopping_plan).map(([storeName, items]) => (
                        items.length > 0 && (
                            <div key={storeName} className="mb-4 p-4 border rounded bg-gray-50">
                                <h3 className="text-xl font-semibold text-gray-800">{storeName}</h3>
                                <ul className="divide-y divide-gray-200">
                                    {items.map((item, itemIndex) => (
                                        <li key={itemIndex} className="py-2 flex justify-between">
                                            <span>{item.product}</span>
                                            <span className="font-mono">${item.price.toFixed(2)}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )
                    ))}
                </div>
            )}
        </div>
    );
};

export default OptimizationResultTile;
