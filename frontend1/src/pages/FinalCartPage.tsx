import React, { useEffect, useState } from 'react';
import { useShoppingList } from '@/context/ShoppingListContext';
import { useStoreSelection } from '@/context/StoreContext';
import { useSubstitutions } from '@/context/SubstitutionContext';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Spinner } from "@/components/ui/spinner"

import fallbackImage from '@/assets/splitcart_symbol_v6.png';

import aldiLogo from '@/assets/ALDI_logo.svg';
import colesLogo from '@/assets/coles_logo.webp';
import igaLogo from '@/assets/iga_logo.webp';
import woolworthsLogo from '@/assets/woolworths_logo.webp';

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

// Logo Mapping
const companyLogos: { [key: string]: string } = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

// Define types for the API response
interface ShoppingPlan {
  [storeName: string]: {
    items: {
      product_name: string;
      brand: string | null;
      size: string;
      quantity: number;
      price: number;
      image_url: string | null;
    }[];
    company_name: string;
    store_address: string;
    total_cost?: number; // Make optional as it's not in best_single_store plan
  };
}

interface OptimizationResult {
  max_stores: number;
  optimized_cost: number;
  savings: number;
  shopping_plan: ShoppingPlan;
}

interface BestSingleStore {
    max_stores: 1;
    optimized_cost: number;
    savings: number;
    shopping_plan: ShoppingPlan;
    items_found_count: number;
    total_items_in_cart: number;
}

interface OptimizationDataSet {
    baseline_cost: number;
    optimization_results: OptimizationResult[];
    best_single_store?: BestSingleStore;
}

interface ApiResponse extends OptimizationDataSet {
  no_subs_results?: OptimizationDataSet;
}

const PlanDetails = ({ plan }: { plan: ShoppingPlan }) => (
    <div className="mt-4 space-y-8">
        {Object.entries(plan).filter(([, store_plan]) => store_plan.items && store_plan.items.length > 0).map(([storeName, store_plan]) => {
            const storeTotal = store_plan.items.reduce((acc, item) => acc + (item.price * item.quantity), 0);
            const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
                e.currentTarget.src = fallbackImage;
            };
            const logo = companyLogos[store_plan.company_name];

            return (
                <div key={storeName} className="border rounded-lg p-4 bg-muted/20">
                    <div className="flex items-center justify-center gap-4 mb-2">
                        {logo && <img src={logo} alt={store_plan.company_name} className="h-10 w-auto" />}
                        <h2 className="text-2xl font-bold">{storeName}</h2>
                    </div>
                    <p className="text-center text-sm text-muted-foreground mb-4">{store_plan.store_address}</p>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[100px]">&nbsp;</TableHead>
                                <TableHead className="text-center">Product</TableHead>
                                <TableHead className="text-center">Quantity</TableHead>
                                <TableHead className="text-right">Unit Price</TableHead>
                                <TableHead className="text-right">Total Price</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {store_plan.items.map((item, index) => (
                                <TableRow key={index}>
                                    <TableCell>
                                        <img 
                                            src={item.image_url || fallbackImage} 
                                            alt={item.product_name} 
                                            className="w-16 h-16 object-cover rounded-md"
                                            onError={handleImageError}
                                        />
                                    </TableCell>
                                    <TableCell className="font-medium text-center">
                                        <div>{item.product_name}</div>
                                        {((item.brand && item.brand !== 'N/A') || item.size) ? (
                                            <div className="text-sm text-muted-foreground flex justify-center items-center mt-1">
                                                {item.brand && item.brand !== 'N/A' && <span>{item.brand}</span>}
                                                {item.brand && item.brand !== 'N/A' && item.size && <span className="mx-1">•</span>}
                                                {item.size && <Badge variant="outline">{item.size}</Badge>}
                                            </div>
                                        ) : null}
                                    </TableCell>
                                    <TableCell className="text-center">{item.quantity}</TableCell>
                                    <TableCell className="text-right">${item.price.toFixed(2)}</TableCell>
                                    <TableCell className="text-right">${(item.price * item.quantity).toFixed(2)}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                        <TableFooter>
                            <TableRow>
                                <TableCell colSpan={4}>Total for {storeName}</TableCell>
                                <TableCell className="text-right">${storeTotal.toFixed(2)}</TableCell>
                            </TableRow>
                        </TableFooter>
                    </Table>
                </div>
            )
        })}
    </div>
);

import { Badge } from "@/components/ui/badge";


const ResultsDisplay = ({ data }: { data: OptimizationDataSet }) => {
    if (!data || (!data.best_single_store && (!data.optimization_results || data.optimization_results.length === 0))) {
        return <p className="mt-4">No optimization results available for this selection.</p>;
    }
    
    const defaultTab = data.best_single_store ? "tab-1" : (data.optimization_results.length > 0 ? `tab-${data.optimization_results[0].max_stores}`: "");

    const highestSavingResult = data.optimization_results.reduce((max, current) => {
        if (!max || current.savings > max.savings) {
            return current;
        }
        return max;
    }, null as OptimizationResult | null);

    return (
        <div className="mt-4">
            <p>Baseline Cost: ${data.baseline_cost.toFixed(2)}</p>
            
            <Tabs defaultValue={defaultTab} className="w-full mt-4">
                <TabsList className="grid w-full grid-cols-4">
                    {data.best_single_store && (
                        <TabsTrigger value="tab-1" className="flex items-center gap-2">
                            <span>Best Single Store</span>
                            <Badge className="bg-blue-500 text-white dark:bg-blue-600">
                                {data.best_single_store.items_found_count}/{data.best_single_store.total_items_in_cart}
                            </Badge>
                        </TabsTrigger>
                    )}
                    {data.optimization_results.map(result => {
                        const percentage = data.baseline_cost > 0 ? Math.round((result.savings / data.baseline_cost) * 100) : 0;
                        const isHighestSaving = highestSavingResult && result.max_stores === highestSavingResult.max_stores;
                        return (
                            <TabsTrigger key={result.max_stores} value={`tab-${result.max_stores}`} className="flex items-center gap-2">
                                <span>{`${result.max_stores} Stores`}</span>
                                {isHighestSaving ? (
                                    <Badge variant="secondary" className="bg-green-500 text-white dark:bg-green-600">
                                        {percentage}%
                                    </Badge>
                                ) : (
                                    <Badge>{percentage}%</Badge>
                                )}
                            </TabsTrigger>
                        )
                    })}
                </TabsList>

                {data.best_single_store && (
                    <TabsContent value="tab-1">
                        <div className="p-4 border rounded-md">
                            <h3 className="font-bold">Total Cost: ${data.best_single_store.optimized_cost.toFixed(2)} (Savings: ${(data.baseline_cost - data.best_single_store.optimized_cost).toFixed(2)})</h3>
                            <p className="text-sm text-muted-foreground">Found {data.best_single_store.items_found_count} of {data.best_single_store.total_items_in_cart} items.</p>
                            <PlanDetails plan={data.best_single_store.shopping_plan} />
                        </div>
                    </TabsContent>
                )}

                {data.optimization_results.map(result => (
                    <TabsContent key={result.max_stores} value={`tab-${result.max_stores}`}>
                        <div className="p-4 border rounded-md">
                            <h3 className="font-bold">Total Cost: ${result.optimized_cost.toFixed(2)} (Savings: ${result.savings.toFixed(2)})</h3>
                            <PlanDetails plan={result.shopping_plan} />
                        </div>
                    </TabsContent>
                ))}
            </Tabs>
        </div>
    );
}

const loadingMessages = [
  "Making the cart go Split",
  "Splitting the cart senseless.",
  "The cart never knew what split it.",
  "Split it and quit it.",
  "Hacking capitalism responsibly.",
  "To Split or not to Split that is the question.",
  "\“The definition of insanity is buying everything from one store.\”\n— Albert Einstein (definitely said this)",
  "Teaching the cart to divide and conquer…",
  "Calculating the most peaceful way to start a price war.",
  "Performing complex cart surgery. Please hold.",
  "Splitting hairs. And carts.",
  "Applying advanced algorithms to banana prices.",
  "Sawing the cart in half.",
  "Split happens...",
  "No carts were harmed in the making of these savings.",
  "Negotiating peace between rival supermarkets.",
  "Optimizing. Strategizing. Slightly judging your shopping list.",
  "\“In the beginning, there was one cart. Then came optimization.\”\n— Genesis of Savings, 3:14",
  "\“Give a man a cart, and he’ll shop for a day. Teach a man to split a cart, and he’ll save for a lifetime.\”\n— Confucius (probably)",
  "\“I came, I saw, I split.\”\n— Julius Caesar",
  "Running a background check on your biscuits.",
  "Balancing taste, price, and your deep emotional attachment to Nutella.",
  "Literally comparing apples to oranges.",
  "Consulting the shopping cart spirits.",
  "Calculating the optimal number of stores to annoy.",
];

const FinalCartPage = () => {
  const { items: originalItems } = useShoppingList();
  const { selectedStoreIds } = useStoreSelection();
  const { selections } = useSubstitutions();
  const [optimizationData, setOptimizationData] = useState<ApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewWithSubstitutes, setViewWithSubstitutes] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState("");

  const selectRandomMessage = () => {
    const randomIndex = Math.floor(Math.random() * loadingMessages.length);
    setLoadingMessage(loadingMessages[randomIndex]);
  };

  useEffect(() => {
    selectRandomMessage(); // Select a random message on initial load
  }, []); // Empty dependency array to run only once

  useEffect(() => {
    if (isLoading) {
      const interval = setInterval(() => {
        selectRandomMessage();
      }, 7000); // 7 seconds

      return () => clearInterval(interval); // Cleanup on unmount or when isLoading changes
    }
  }, [isLoading]);

  useEffect(() => {
    const optimizeCart = async () => {
      if (originalItems.length === 0 || selectedStoreIds.size === 0) {
        setIsLoading(false);
        return;
      }

      const cart = originalItems.map(item => {
        const original_item_option = { product_id: item.product.id, quantity: item.quantity };
        const subs = selections[item.product.id];
        if (subs && subs.length > 0) {
            const sub_options = subs.map(sub => ({ product_id: sub.product.id, quantity: sub.quantity }));
            return [original_item_option, ...sub_options];
        }
        return [original_item_option];
      });

      const original_items_payload = originalItems.map(item => ({
        product: { id: item.product.id },
        quantity: item.quantity,
      }));

      const payload = {
        cart: cart,
        store_ids: Array.from(selectedStoreIds),
        original_items: original_items_payload,
        max_stores_options: [2, 3, 4], // Starts from 2 as 1 is handled by best_single_store
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

  if (isLoading) {
    return (
      <div className="container mx-auto p-4 flex flex-col items-center justify-center text-center" style={{ minHeight: 'calc(100vh - 10rem)' }}>
        <h1 className="text-2xl font-bold mb-4" style={{ whiteSpace: 'pre-line' }}>{loadingMessage}</h1>
        <Spinner />
      </div>
    );
  }
  if (error) return <div className="container mx-auto p-4">Error: {error}</div>;
  if (!optimizationData) return <div className="container mx-auto p-4">No optimization data available. Add items to your cart and select stores.</div>;

  const resultsToShow = viewWithSubstitutes ? optimizationData : optimizationData.no_subs_results;

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Cart Optimization Results</h1>
        {optimizationData.no_subs_results && (
            <div className="flex items-center space-x-2">
                <Switch id="substitutes-switch" checked={viewWithSubstitutes} onCheckedChange={setViewWithSubstitutes} className={viewWithSubstitutes ? 'data-[state=checked]:bg-green-500' : ''} />
                <Label htmlFor="substitutes-switch">Include Substitutes</Label>
            </div>
        )}
      </div>
      
      {resultsToShow ? <ResultsDisplay data={resultsToShow} /> : <p>No results to display for this option.</p>}

    </div>
  );
};

export default FinalCartPage;