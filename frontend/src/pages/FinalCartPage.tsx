import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '@/context/CartContext';
import { useStoreList } from '@/context/StoreListContext';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import LoadingSpinner from '@/components/LoadingSpinner';
import ResultsDisplay from '@/components/ResultsDisplay';
import { FaqAccordion } from '@/components/FaqAccordion';
import { FaqImageSection } from "../components/FaqImageSection";
import futureTodayImage from "@/assets/future_today.png";
import type { ApiResponse, ExportData } from '@/types';

const FinalCartPage = () => {
  const { currentCart, optimizationResult, setOptimizationResult } = useCart();
  const { selectedStoreIds } = useStoreList();
  const { isAuthenticated, token } = useAuth();
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(false); // Optimization is done on previous page
  const [error, setError] = useState<string | null>(null);
  const [viewWithSubstitutes, setViewWithSubstitutes] = useState(true);
  const [exportAction, setExportAction] = useState<{type: 'email' | 'download', plan: string} | null>(null);

  // Clear optimization results if cart or stores change, or on unmount
  useEffect(() => {
    return () => {
      setOptimizationResult(null);
    };
  }, [currentCart, selectedStoreIds, setOptimizationResult]);

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

  // The optimization data is now passed via CartContext from SubstitutionPage
  useEffect(() => {
    if (!optimizationResult && currentCart?.items.length === 0) {
      // If no optimization result and cart is empty, navigate home
      navigate('/');
    } else if (!optimizationResult) {
      // If no optimization result but cart has items, navigate to substitutions to trigger optimization
      navigate('/substitutions');
    }
  }, [optimizationResult, currentCart, navigate]);

  if (isLoading) {
    return <LoadingSpinner />;
  }
  if (error && !exportAction) return <div className="container mx-auto p-4">Error: {error}</div>;
  if (!optimizationResult) return <div className="container mx-auto p-4">No optimization data available. Please go through the substitution process.</div>;

  const resultsToShow = viewWithSubstitutes ? optimizationResult : optimizationResult.no_subs_results;

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Cart Optimization Results</h1>
        {optimizationResult.no_subs_results && (
            <div className="flex items-center space-x-2">
                <Switch id="substitutes-switch" checked={viewWithSubstitutes} onCheckedChange={setViewWithSubstitutes} className={viewWithSubstitutes ? 'data-[state=checked]:bg-green-500' : ''} />
                <Label htmlFor="substitutes-switch">Include Substitutes</Label>
            </div>
        )}
      </div>

      {resultsToShow ? <ResultsDisplay data={resultsToShow} handleDownload={handleDownload} handleEmail={handleEmail} exportAction={exportAction} /> : <p>No results to display for this option.</p>}

      <div className="mt-16">
        <FaqImageSection
          title="Helpful Information"
          page="final_cart"
          imageSrc={futureTodayImage}
          imageAlt="The future is today"
        />
      </div>

    </div>
  );
};

export default FinalCartPage;