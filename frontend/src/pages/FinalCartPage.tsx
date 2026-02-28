import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useStoreList } from '../context/StoreListContext';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { Switch } from "../components/ui/switch"
import { Label } from "../components/ui/label"
import LoadingSpinner from '../components/LoadingSpinner';
import ResultsDisplay from '../components/ResultsDisplay';
import { FAQ } from "../components/FAQ";
import futureTodayImage from "../assets/future_today.webp";
import type { ExportData } from '../types';

const finalCartFaqs = [
  {"question": "How is baseline cost calculated?", "answer": "By taking each item in your list, finding the average price across all available stores, and then summing up these average prices for all items. We use this method, not because it shows the highest savings, but because we believe it is realistic, transparent and honest."},
  {"question": "What is the \"Best Single Store\" option?", "answer": "The cheapest total price if you bought everything at just one store. We find the single store that has the most items on your list for the lowest price, giving you a clear benchmark for your savings."},
  {"question": "How can I maximize my savings with SplitCart?", "answer": "Approve more substitutes and/or approve more stores. For example, consider adding stores near your work or on your way home not just close to home."}
];

const FinalCartPage = () => {
  const { optimizationResult, currentCart, emailCurrentCart, downloadCurrentCart } = useCart();
  useStoreList();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [isLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewWithSubstitutes, setViewWithSubstitutes] = useState(true);
  const [exportAction, setExportAction] = useState<{type: 'email' | 'download', plan: string} | null>(null);

  const handleEmail = async (exportData: ExportData, planName: string) => {
    if (!isAuthenticated) {
      toast.error("Authentication Required", {
        description: "Please log in to email your shopping list.",
        action: { label: "Login", onClick: () => navigate("/login") },
      });
      return;
    }
    setExportAction({type: 'email', plan: planName});
    setError(null);
    try {
      await emailCurrentCart(exportData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setExportAction(null);
    }
  };

  const handleDownload = async (exportData: ExportData, planName: string) => {
    setExportAction({type: 'download', plan: planName});
    setError(null);
    try {
      const blob = await downloadCurrentCart(exportData);
      if (!blob) return;
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
    } finally {
      setExportAction(null);
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error && !exportAction) return <div className="container mx-auto p-4">Error: {error}</div>;
  if (!optimizationResult) return <div className="container mx-auto p-4">No optimization data available. Please go through the substitution process.</div>;

  const resultsToShow = viewWithSubstitutes ? optimizationResult : optimizationResult.no_subs_results;

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Your Optimised Cart</h1>
          <p className="text-gray-500 mt-1">Here's the cheapest way to buy your list.</p>
        </div>
        {optimizationResult.no_subs_results && (
          <div className="flex items-center gap-3 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 self-start sm:self-auto">
            <Switch
              id="substitutes-switch"
              checked={viewWithSubstitutes}
              onCheckedChange={setViewWithSubstitutes}
              className={viewWithSubstitutes ? 'data-[state=checked]:bg-green-500' : ''}
            />
            <Label htmlFor="substitutes-switch" className="font-medium cursor-pointer select-none">
              Include Substitutes
            </Label>
          </div>
        )}
      </div>

      {resultsToShow && currentCart
        ? <ResultsDisplay cart={currentCart} data={resultsToShow} handleDownload={handleDownload} handleEmail={handleEmail} exportAction={exportAction} />
        : <p className="text-gray-500">No results to display for this option.</p>
      }

      <div className="mt-16">
        <FAQ
          title="Helpful Information"
          faqs={finalCartFaqs}
          imageSrc={futureTodayImage}
          imageAlt="The future is today"
        />
      </div>
    </div>
  );
};

export default FinalCartPage;
