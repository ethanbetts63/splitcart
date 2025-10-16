import React, { useEffect, useState } from 'react';
import { useShoppingList } from '@/context/ShoppingListContext';
import { useStoreSelection } from '@/context/StoreContext';
import { useSubstitutions } from '@/context/SubstitutionContext';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

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

interface BestSingleStore {
    store_name: string;
    total_cost: number;
    items: any[];
}

interface OptimizationDataSet {
    baseline_cost: number;
    optimization_results: OptimizationResult[];
    best_single_store?: BestSingleStore;
}

interface ApiResponse extends OptimizationDataSet {
  no_subs_results?: OptimizationDataSet;
}

const FinalCartPage = () => {
  const { items: originalItems } = useShoppingList();
  const { selectedStoreIds } = useStoreSelection();
  const { selections } = useSubstitutions();
  const [optimizationData, setOptimizationData] = useState<ApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewWithSubstitutes, setViewWithSubstitutes] = useState(true);

  useEffect(() => {
    const optimizeCart = async () => {
      if (originalItems.length === 0 || selectedStoreIds.size === 0) {
        setIsLoading(false);
        return;
      }

      const cart = originalItems.map(item => {
        const subs = selections[item.product.id];
        if (subs && subs.length > 0) {
          return subs.map(sub => ({ product_id: sub.product.id, quantity: sub.quantity }));
        }
        return [{ product_id: item.product.id, quantity: item.quantity }];
      });

      const original_items_payload = originalItems.map(item => ({
        product: { id: item.product.id },
        quantity: item.quantity,
      }));

      const payload = {
        cart: cart,
        store_ids: Array.from(selectedStoreIds),
        original_items: original_items_payload,
        max_stores_options: [1, 2, 3, 4],
      };

      try {
        setIsLoading(true);
        const response = await fetch('/api/cart/split/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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

  const renderResults = (data: OptimizationDataSet) => {
    if (!data || !data.optimization_results || data.optimization_results.length === 0) {
        return <p className="mt-4">No optimization results available for this selection.</p>;
    }
    const defaultTab = `tab-${data.optimization_results[0].max_stores}`;

    return (
        <div className="mt-4">
            <p>Baseline Cost (most common price): ${data.baseline_cost.toFixed(2)}</p>
            {data.best_single_store && typeof data.best_single_store.total_cost === 'number' && (
                <p>Best single store ({data.best_single_store.store_name}) cost: ${data.best_single_store.total_cost.toFixed(2)}</p>
            )}

            <Tabs defaultValue={defaultTab} className="w-full mt-4">
                <TabsList className="grid w-full grid-cols-4">
                    {data.optimization_results.map(result => {
                        const tabName = result.max_stores === 1 ? 'Best Single Store' : `${result.max_stores} Stores`;
                        return (
                            <TabsTrigger key={result.max_stores} value={`tab-${result.max_stores}`}>
                                {tabName}
                            </TabsTrigger>
                        )
                    })}
                </TabsList>

                {data.optimization_results.map(result => (
                    <TabsContent key={result.max_stores} value={`tab-${result.max_stores}`}>
                        <div className="p-4 border rounded-md">
                            <h3 className="font-bold">Total Cost: ${result.optimized_cost.toFixed(2)} (Savings: ${result.savings.toFixed(2)})</h3>
                            <div className="mt-2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {Object.entries(result.shopping_plan).map(([storeName, plan]) => (
                                    <div key={storeName} className="border p-2 rounded-md bg-muted/20">
                                        <h4 className="font-semibold">{storeName} {typeof plan.total_cost === 'number' && `(${plan.total_cost.toFixed(2)})`}</h4>
                                        <ul className="list-disc pl-5 mt-1">
                                            {plan.items.map((item, index) => (
                                                <li key={index} className="text-sm">
                                                    {item.product_name} (x{item.quantity}) - {typeof item.price === 'number' ? `$${item.price.toFixed(2)}` : 'N/A'}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </TabsContent>
                ))}
            </Tabs>
        </div>
    );
  }

  if (isLoading) return <div className="container mx-auto p-4">Loading optimization results...</div>;
  if (error) return <div className="container mx-auto p-4">Error: {error}</div>;
  if (!optimizationData) return <div className="container mx-auto p-4">No optimization data available. Add items to your cart and select stores.</div>;

  const resultsToShow = viewWithSubstitutes ? optimizationData : optimizationData.no_subs_results;

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Cart Optimization Results</h1>
        {optimizationData.no_subs_results && (
            <div className="flex items-center space-x-2">
                <Switch id="substitutes-switch" checked={viewWithSubstitutes} onCheckedChange={setViewWithSubstitutes} />
                <Label htmlFor="substitutes-switch">Include Substitutes</Label>
            </div>
        )}
      </div>
      
      {resultsToShow ? renderResults(resultsToShow) : <p>No results to display for this option.</p>}

    </div>
  );
};

export default FinalCartPage;