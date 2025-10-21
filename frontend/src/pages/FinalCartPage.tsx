import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShoppingList } from '@/context/ShoppingListContext';
import { useStoreSelection } from '@/context/StoreContext';
import { useSubstitutions } from '@/context/SubstitutionContext';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import LoadingSpinner from '@/components/LoadingSpinner';
import ResultsDisplay from '@/components/ResultsDisplay';
import type { ApiResponse, ExportData } from '@/types';

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
      
import { FaqAccordion } from '@/components/FaqAccordion';
import { AspectRatio } from "@/components/ui/aspect-ratio";
import kingKongImage from "../assets/king_kong.png";

// ... (rest of the imports)

// ... (rest of the component)

      {resultsToShow ? <ResultsDisplay data={resultsToShow} handleDownload={handleDownload} handleEmail={handleEmail} exportAction={exportAction} /> : <p>No results to display for this option.</p>}

      <div className="mt-16">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">Cart FAQs</h2>
            <FaqAccordion page="final_cart" />
          </div>
          <div>
            <AspectRatio ratio={16 / 9}>
              <img src={kingKongImage} alt="King Kong swatting at discount planes" className="rounded-md object-contain w-full h-full" />
            </AspectRatio>
          </div>
        </div>
      </div>

    </div>
  );
};

export default FinalCartPage;