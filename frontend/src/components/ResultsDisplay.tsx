import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Download, Mail } from "lucide-react";
import { Spinner } from "./ui/spinner";
import PlanDetails from './PlanDetails';
import * as types from '../types';

const ResultsDisplay = ({ cart, data, handleDownload, handleEmail, exportAction }: {
  cart: types.Cart;
  data: types.OptimizationDataSet;
  handleDownload: (exportData: types.ExportData, planName: string) => Promise<void>;
  handleEmail: (exportData: types.ExportData, planName: string) => Promise<void>;
  exportAction: {type: 'email' | 'download', plan: string} | null;
}) => {
  if (!data || (!data.best_single_store && (!data.optimization_results || data.optimization_results.length === 0))) {
    return <p className="mt-4 text-gray-500">No optimization results available for this selection.</p>;
  }

  let singleStoreBaselineCost = 0;
  let singleStoreSavings = 0;

  if (data.best_single_store && cart) {
    const singleStoreProducts = new Set<string>();
    const plan = data.best_single_store.shopping_plan;
    for (const storeName in plan) {
      plan[storeName].items.forEach(item => {
        singleStoreProducts.add(`${item.product_name}|${item.brand || 'null'}|${item.size || ''}`);
      });
    }
    singleStoreBaselineCost = cart.items.reduce((total, cartItem) => {
      const id = `${cartItem.product.name}|${cartItem.product.brand_name || 'null'}|${cartItem.product.size || ''}`;
      if (singleStoreProducts.has(id) && cartItem.baseline_price) {
        return total + (cartItem.baseline_price * cartItem.quantity);
      }
      return total;
    }, 0);
    singleStoreSavings = singleStoreBaselineCost > 0 ? singleStoreBaselineCost - data.best_single_store.optimized_cost : 0;
  }

  const defaultTab = data.best_single_store ? "tab-1" : (data.optimization_results.length > 0 ? `tab-${data.optimization_results[0].max_stores}` : "");

  const highestSavingResult = data.optimization_results.reduce((max, current) => {
    if (!max || current.savings > max.savings) return current;
    return max;
  }, null as types.OptimizationResult | null);

  const ExportButtons = ({ onEmail, onDownload, planKey }: { onEmail: () => void; onDownload: () => void; planKey: string }) => (
    <div className="flex items-center gap-2">
      <button
        onClick={onEmail}
        disabled={exportAction?.type === 'email' && exportAction?.plan === planKey}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold border border-gray-300 bg-white rounded-lg hover:border-gray-900 hover:text-gray-900 transition-colors duration-150 disabled:opacity-50"
      >
        {exportAction?.type === 'email' && exportAction?.plan === planKey
          ? <Spinner className="h-4 w-4 animate-spin" />
          : <Mail className="h-4 w-4" />
        }
        Email
      </button>
      <button
        onClick={onDownload}
        disabled={exportAction?.type === 'download' && exportAction?.plan === planKey}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold border border-gray-300 bg-white rounded-lg hover:border-gray-900 hover:text-gray-900 transition-colors duration-150 disabled:opacity-50"
      >
        {exportAction?.type === 'download' && exportAction?.plan === planKey
          ? <Spinner className="h-4 w-4 animate-spin" />
          : <Download className="h-4 w-4" />
        }
        Download
      </button>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Baseline cost */}
      <div className="rounded-xl border border-gray-200 bg-gray-50 px-5 py-4 flex flex-wrap items-center gap-x-6 gap-y-1">
        <span className="text-sm text-gray-500">Baseline cost (average across stores)</span>
        <span className="font-bold text-gray-900 text-lg">${data.baseline_cost.toFixed(2)}</span>
      </div>

      <Tabs defaultValue={defaultTab} className="w-full">
        {/* Tab List */}
        <TabsList className="flex h-auto w-full gap-1.5 bg-transparent p-0 flex-wrap">
          {data.best_single_store && (
            <TabsTrigger
              value="tab-1"
              className="flex-1 min-w-[120px] flex flex-col items-center gap-0.5 rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm font-semibold text-gray-600 shadow-sm transition-all data-[state=active]:border-yellow-400 data-[state=active]:bg-yellow-300 data-[state=active]:text-black data-[state=active]:shadow-none"
            >
              <span>Best Single Store</span>
              <span className="text-xs font-normal opacity-70">
                {data.best_single_store.items_found_count}/{data.best_single_store.total_items_in_cart} items
              </span>
            </TabsTrigger>
          )}
          {data.optimization_results.map(result => {
            const percentage = data.baseline_cost > 0 ? Math.round((result.savings / data.baseline_cost) * 100) : 0;
            const isHighestSaving = highestSavingResult && result.max_stores === highestSavingResult.max_stores;
            return (
              <TabsTrigger
                key={result.max_stores}
                value={`tab-${result.max_stores}`}
                className={`flex-1 min-w-[100px] flex flex-col items-center gap-0.5 rounded-xl border px-3 py-2.5 text-sm font-semibold shadow-sm transition-all data-[state=active]:shadow-none ${
                  isHighestSaving
                    ? 'border-green-300 bg-green-50 text-green-800 data-[state=active]:border-green-500 data-[state=active]:bg-green-500 data-[state=active]:text-white'
                    : 'border-gray-200 bg-white text-gray-600 data-[state=active]:border-yellow-400 data-[state=active]:bg-yellow-300 data-[state=active]:text-black'
                }`}
              >
                <span>{result.max_stores} Stores</span>
                <span className="text-xs font-bold">{percentage > 0 ? `Save ${percentage}%` : '—'}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {/* Best Single Store Panel */}
        {data.best_single_store && (
          <TabsContent value="tab-1" className="mt-4">
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
              <div className="p-5 border-b border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-8">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Total Cost</p>
                    <p className="text-2xl font-bold text-gray-900">${data.best_single_store.optimized_cost.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">You Save</p>
                    <p className="text-2xl font-bold text-green-600">${singleStoreSavings.toFixed(2)}</p>
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <ExportButtons
                    planKey="best-single-store"
                    onEmail={() => handleEmail({ shopping_plan: data.best_single_store!.shopping_plan, baseline_cost: singleStoreBaselineCost, optimized_cost: data.best_single_store!.optimized_cost, savings: singleStoreSavings }, 'best-single-store')}
                    onDownload={() => handleDownload({ shopping_plan: data.best_single_store!.shopping_plan, baseline_cost: singleStoreBaselineCost, optimized_cost: data.best_single_store!.optimized_cost, savings: singleStoreSavings }, 'best-single-store')}
                  />
                  <p className="text-xs text-gray-400">Found {data.best_single_store.items_found_count} of {data.best_single_store.total_items_in_cart} items</p>
                </div>
              </div>
              <PlanDetails plan={data.best_single_store.shopping_plan} />
            </div>
          </TabsContent>
        )}

        {/* Optimization Result Panels */}
        {data.optimization_results.map(result => (
          <TabsContent key={result.max_stores} value={`tab-${result.max_stores}`} className="mt-4">
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
              <div className="p-5 border-b border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-8">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Total Cost</p>
                    <p className="text-2xl font-bold text-gray-900">${result.optimized_cost.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">You Save</p>
                    <p className="text-2xl font-bold text-green-600">${result.savings.toFixed(2)}</p>
                  </div>
                </div>
                <ExportButtons
                  planKey={`stores-${result.max_stores}`}
                  onEmail={() => handleEmail({ shopping_plan: result.shopping_plan, baseline_cost: data.baseline_cost, optimized_cost: result.optimized_cost, savings: result.savings }, `stores-${result.max_stores}`)}
                  onDownload={() => handleDownload({ shopping_plan: result.shopping_plan, baseline_cost: data.baseline_cost, optimized_cost: result.optimized_cost, savings: result.savings }, `stores-${result.max_stores}`)}
                />
              </div>
              <PlanDetails plan={result.shopping_plan} />
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
};

export default ResultsDisplay;
