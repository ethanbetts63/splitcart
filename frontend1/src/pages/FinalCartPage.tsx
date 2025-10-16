import React, { useEffect, useState } from 'react';
import { useShoppingList } from '@/context/ShoppingListContext';
import { useStoreSelection } from '@/context/StoreContext';
import { useSubstitutions } from '@/context/SubstitutionContext';
import type { CartItem } from '@/types/CartItem';

// Define types for the API response
interface ShoppingPlan {
  [storeName: string]: {
    items: {
      product_name: string;
      quantity: number;
      price: number;
    }[];
    total_cost: number;
  };
}

interface OptimizationResult {
  max_stores: number;
  optimized_cost: number;
  savings: number;
  shopping_plan: ShoppingPlan;
}

interface ApiResponse {
  baseline_cost: number;
  optimization_results: OptimizationResult[];
  best_single_store: {
    store_name: string;
    total_cost: number;
    items: any[];
  };
  no_subs_results?: {
    baseline_cost: number;
    optimization_results: OptimizationResult[];
    best_single_store: {
      store_name: string;
      total_cost: number;
      items: any[];
    };
  }
}

const FinalCartPage = () => {
  const { items: originalItems } = useShoppingList();
  const { selectedStoreIds } = useStoreSelection();
  const { selections } = useSubstitutions();
  const [optimizationData, setOptimizationData] = useState<ApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const optimizeCart = async () => {
      if (originalItems.length === 0 || selectedStoreIds.size === 0) {
        setIsLoading(false);
        return;
      }

      // Construct the 'cart' payload
      const cart = originalItems.map(item => {
        const subs = selections[item.product.id];
        if (subs && subs.length > 0) {
          return subs.map(sub => ({
            product_id: sub.product.id,
            quantity: sub.quantity,
          }));
        }
        return [{ product_id: item.product.id, quantity: item.quantity }];
      });

      // Construct the 'original_items' payload for no-subs calculation
      const original_items_payload = originalItems.map(item => ({
        product: { id: item.product.id },
        quantity: item.quantity,
      }));

      const payload = {
        cart: cart,
        store_ids: Array.from(selectedStoreIds),
        original_items: original_items_payload,
        max_stores_options: [1, 2, 3],
      };

      try {
        const response = await fetch('/api/cart/split/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            // Add CSRF token header if needed
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to optimize cart');
        }

        const data: ApiResponse = await response.json();
        setOptimizationData(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    optimizeCart();
  }, [originalItems, selectedStoreIds, selections]);

  if (isLoading) {
    return <div>Loading optimization results...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!optimizationData) {
    return <div>No optimization data available. Add items to your cart and select stores.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Cart Optimization Results</h1>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold">With Substitutions</h2>
        <p>Baseline Cost (if you bought everything at its most common price): ${optimizationData.baseline_cost.toFixed(2)}</p>
        {optimizationData.best_single_store && typeof optimizationData.best_single_store.total_cost === 'number' && (
            <p>Best single store ({optimizationData.best_single_store.store_name}) cost: ${optimizationData.best_single_store.total_cost.toFixed(2)}</p>
        )}

        {optimizationData.optimization_results.map(result => (
          <div key={result.max_stores} className="mt-4 p-4 border rounded">
            <h3 className="font-bold">Split between {result.max_stores} stores</h3>
            <p>Total Cost: ${result.optimized_cost.toFixed(2)}</p>
            <p>Savings: ${result.savings.toFixed(2)}</p>
            <div>
              {Object.entries(result.shopping_plan).map(([storeName, plan]) => (
                <div key={storeName} className="mt-2">
                  <h4 className="font-semibold">{storeName} (${plan.total_cost.toFixed(2)})</h4>
                  <ul>
                    {plan.items.map((item, index) => (
                      <li key={index}>{item.product_name} (x{item.quantity}) - ${item.price.toFixed(2)}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {optimizationData.no_subs_results && (
        <div>
          <h2 className="text-xl font-semibold">Without Substitutions</h2>
           <p>Baseline Cost: ${optimizationData.no_subs_results.baseline_cost.toFixed(2)}</p>
           {optimizationData.no_subs_results.best_single_store && typeof optimizationData.no_subs_results.best_single_store.total_cost === 'number' && (
            <p>Best single store ({optimizationData.no_subs_results.best_single_store.store_name}) cost: ${optimizationData.no_subs_results.best_single_store.total_cost.toFixed(2)}</p>
        )}
          {optimizationData.no_subs_results.optimization_results.map(result => (
            <div key={result.max_stores} className="mt-4 p-4 border rounded">
              <h3 className="font-bold">Split between {result.max_stores} stores</h3>
              <p>Total Cost: ${result.optimized_cost.toFixed(2)}</p>
              <p>Savings: ${result.savings.toFixed(2)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FinalCartPage;