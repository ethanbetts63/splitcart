import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShoppingList } from '@/context/ShoppingListContext';
import { useStoreSelection } from '@/context/StoreContext';
import { useSubstitutions } from '@/context/SubstitutionContext';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button";
import { Download, Mail } from "lucide-react";
import { Spinner } from "@/components/ui/spinner"
import LoadingSpinner from '@/components/LoadingSpinner';

import fallbackImage from '@/assets/splitcart_symbol_v6.png';

import aldiLogo from '@/assets/ALDI_logo.svg';
import colesLogo from '@/assets/coles_logo.webp';
import igaLogo from '@/assets/iga_logo.webp';
import woolworthsLogo from '@/assets/woolworths_logo.webp';

import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge";

// Logo Mapping
import PlanDetails from '@/components/PlanDetails';


const ResultsDisplay = ({ data, handleDownload, handleEmail, exportAction }: {
    data: OptimizationDataSet;
    handleDownload: (exportData: ExportData, planName: string) => Promise<void>;
    handleEmail: (exportData: ExportData, planName: string) => Promise<void>;
    exportAction: {type: 'email' | 'download', plan: string} | null;
}) => {
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
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="font-bold text-lg">Total Cost: ${data.best_single_store.optimized_cost.toFixed(2)}</h3>
                                    <p className="text-sm text-green-600 font-semibold">Savings: ${(data.baseline_cost - data.best_single_store.optimized_cost).toFixed(2)}</p>
                                    <p className="text-sm text-muted-foreground mt-1">Found {data.best_single_store.items_found_count} of {data.best_single_store.total_items_in_cart} items.</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button 
                                        variant="outline" 
                                        size="sm"
                                        onClick={() => handleEmail({ shopping_plan: data.best_single_store.shopping_plan, baseline_cost: data.baseline_cost, optimized_cost: data.best_single_store.optimized_cost, savings: data.best_single_store.savings }, 'best-single-store')}
                                        disabled={exportAction?.type === 'email' && exportAction?.plan === 'best-single-store'}
                                    >
                                        {exportAction?.type === 'email' && exportAction?.plan === 'best-single-store' ? (
                                            <Spinner className="mr-2 h-4 w-4 animate-spin" />
                                        ) : (
                                            <Mail className="mr-2 h-4 w-4" />
                                        )}
                                        <span>Email</span>
                                    </Button>
                                    <Button 
                                        variant="outline" 
                                        size="sm"
                                        onClick={() => handleDownload({ shopping_plan: data.best_single_store.shopping_plan, baseline_cost: data.baseline_cost, optimized_cost: data.best_single_store.optimized_cost, savings: data.best_single_store.savings }, 'best-single-store')}
                                        disabled={exportAction?.type === 'download' && exportAction?.plan === 'best-single-store'}
                                    >
                                        {exportAction?.type === 'download' && exportAction?.plan === 'best-single-store' ? (
                                            <Spinner className="mr-2 h-4 w-4 animate-spin" />
                                        ) : (
                                            <Download className="mr-2 h-4 w-4" />
                                        )}
                                        <span>Download</span>
                                    </Button>
                                </div>
                            </div>
                            <PlanDetails plan={data.best_single_store.shopping_plan} />
                        </div>
                    </TabsContent>
                )}

                {data.optimization_results.map(result => (
                    <TabsContent key={result.max_stores} value={`tab-${result.max_stores}`}>
                        <div className="p-4 border rounded-md">
                            <div className="flex justify-between items-center mb-4">
                                <div>
                                    <h3 className="font-bold text-lg">Total Cost: ${result.optimized_cost.toFixed(2)}</h3>
                                    <p className="text-sm text-green-600 font-semibold">Savings: ${result.savings.toFixed(2)}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button 
                                        variant="outline" 
                                        size="sm"
                                        onClick={() => handleEmail({ shopping_plan: result.shopping_plan, baseline_cost: data.baseline_cost, optimized_cost: result.optimized_cost, savings: result.savings }, `stores-${result.max_stores}`)}
                                        disabled={exportAction?.type === 'email' && exportAction?.plan === `stores-${result.max_stores}`}
                                    >
                                        {exportAction?.type === 'email' && exportAction?.plan === `stores-${result.max_stores}` ? (
                                            <Spinner className="mr-2 h-4 w-4 animate-spin" />
                                        ) : (
                                            <Mail className="mr-2 h-4 w-4" />
                                        )}
                                        <span>Email</span>
                                    </Button>
                                    <Button 
                                        variant="outline" 
                                        size="sm"
                                        onClick={() => handleDownload({ shopping_plan: result.shopping_plan, baseline_cost: data.baseline_cost, optimized_cost: result.optimized_cost, savings: result.savings }, `stores-${result.max_stores}`)}
                                        disabled={exportAction?.type === 'download' && exportAction?.plan === `stores-${result.max_stores}`}
                                    >
                                        {exportAction?.type === 'download' && exportAction?.plan === `stores-${result.max_stores}` ? (
                                            <Spinner className="mr-2 h-4 w-4 animate-spin" />
                                        ) : (
                                            <Download className="mr-2 h-4 w-4" />
                                        )}
                                        <span>Download</span>
                                    </Button>
                                </div>
                            </div>
                            <PlanDetails plan={result.shopping_plan} />
                        </div>
                    </TabsContent>
                ))}
            </Tabs>
        </div>
    );
}

const FinalCartPage = () => {
  const { items: originalItems } = useShoppingList();
  const { selectedStoreIds } = useStoreSelection();
  const { selections } = useSubstitutions();
  const { isAuthenticated, token } = useAuth();
  const navigate = useNavigate();

  const [optimizationData, setOptimizationData] = useState<ApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewWithSubstitutes, setViewWithSubstitutes] = useState(true);
  const [exportAction, setExportAction] = useState<{type: 'email' | 'download', plan: string} | null>(null);

  const handleEmail = async (exportData: ExportData, planName: string) => {
    if (!isAuthenticated) {
        toast.error("Authentication Required", {
            description: "Please log in to email your shopping list.",
            action: {
                label: "Login",
                onClick: () => navigate("/login"),
            },
        });
        return;
    }

    setExportAction({type: 'email', plan: planName});
    setError(null);

    try {
        const response = await fetch('/api/cart/email-list/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`
            },
            body: JSON.stringify(exportData),
        });

        const resData = await response.json();

        if (!response.ok) {
            throw new Error(resData.error || `Server returned an unexpected error (${response.status}).`);
        }
        
toast.success("Email Sent!", {
            description: "Your shopping list has been sent to your email.",
        });

    } catch (err: any) {
        setError(err.message);
        toast.error("Error Sending Email", {
            description: err.message,
        });
    } finally {
        setExportAction(null);
    }
  };

  const handleDownload = async (exportData: ExportData, planName: string) => {
    setExportAction({type: 'download', plan: planName});
    setError(null);

    try {
        const response = await fetch('/api/cart/download-list/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(exportData),
        });

        if (!response.ok) {
            const contentType = response.headers.get("content-type");
            let errorMessage = 'Failed to generate PDF.';
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } else {
                errorMessage = `Server returned an unexpected error (${response.status}).`;
            }
            throw new Error(errorMessage);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `splitcart-plan-${planName}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

    } catch (err: any) {
        setError(err.message);
        toast.error("Error Downloading PDF", {
            description: err.message,
        });
    } finally {
        setExportAction(null);
    }
  };

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
        max_stores_options: [2, 3, 4],
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
    return <LoadingSpinner />;
  }
  if (error && !exportAction) return <div className="container mx-auto p-4">Error: {error}</div>;
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
      
      {resultsToShow ? <ResultsDisplay data={resultsToShow} handleDownload={handleDownload} handleEmail={handleEmail} exportAction={exportAction} /> : <p>No results to display for this option.</p>}

    </div>
  );
};

export default FinalCartPage;
st.success("Email Sent!", {
            description: "Your shopping list has been sent to your email.",
        });

    } catch (err: any) {
        setError(err.message);
        toast.error("Error Sending Email", {
            description: err.message,
        });
    } finally {
        setExportAction(null);
    }
  };

  const handleDownload = async (plan: ShoppingPlan, planName: string) => {
    setExportAction({type: 'download', plan: planName});
    setError(null);

    try {
        const response = await fetch('/api/cart/download-list/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ shopping_plan: plan }),
        });

        if (!response.ok) {
            const contentType = response.headers.get("content-type");
            let errorMessage = 'Failed to generate PDF.';
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } else {
                errorMessage = `Server returned an unexpected error (${response.status}).`;
            }
            throw new Error(errorMessage);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `splitcart-plan-${planName}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

    } catch (err: any) {
        setError(err.message);
        toast.error("Error Downloading PDF", {
            description: err.message,
        });
    } finally {
        setExportAction(null);
    }
  };

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
        max_stores_options: [2, 3, 4],
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
    return <LoadingSpinner />;
  }
  if (error && !exportAction) return <div className="container mx-auto p-4">Error: {error}</div>;
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
      
      {resultsToShow ? <ResultsDisplay data={resultsToShow} handleDownload={handleDownload} handleEmail={handleEmail} exportAction={exportAction} /> : <p>No results to display for this option.</p>}

    </div>
  );
};

export default FinalCartPage;