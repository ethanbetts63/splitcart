import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Download, Mail } from 'lucide-react';
import { Spinner } from './ui/spinner';
import PlanDetails from './PlanDetails';
import { cva } from 'class-variance-authority';

import * as types from '../types';

/**
 * Hoisted to module scope on purpose: a component declared inside another
 * component's body is a new component type on every render, so React unmounts
 * and remounts its subtree instead of updating it (react-hooks/static-components).
 * `exportAction` therefore arrives as a prop rather than a closure.
 */
const ExportButtons = ({
  onEmail,
  onDownload,
  planKey,
  exportAction,
}: {
  onEmail: () => void;
  onDownload: () => void;
  planKey: string;
  exportAction: types.ExportAction | null;
}) => (
  <div className="flex items-center gap-2">
    <button
      onClick={onEmail}
      disabled={exportAction?.type === 'email' && exportAction?.plan === planKey}
      className="flex items-center gap-1.5 px-3 py-1.5 text-body font-semibold border border-border-strong bg-surface-page rounded-lg hover:border-border-strong-hover hover:text-text-primary transition-colors duration-150 disabled:opacity-50"
    >
      {exportAction?.type === 'email' && exportAction?.plan === planKey ? (
        <Spinner className="h-4 w-4 animate-spin" />
      ) : (
        <Mail className="h-4 w-4" />
      )}
      Email
    </button>
    <button
      onClick={onDownload}
      disabled={exportAction?.type === 'download' && exportAction?.plan === planKey}
      className="flex items-center gap-1.5 px-3 py-1.5 text-body font-semibold border border-border-strong bg-surface-page rounded-lg hover:border-border-strong-hover hover:text-text-primary transition-colors duration-150 disabled:opacity-50"
    >
      {exportAction?.type === 'download' && exportAction?.plan === planKey ? (
        <Spinner className="h-4 w-4 animate-spin" />
      ) : (
        <Download className="h-4 w-4" />
      )}
      Download
    </button>
  </div>
);

/**
 * The plan tabs: three states (resting, active, and "this is the biggest
 * saving") across two palettes, previously a multi-branch ternary inside a
 * template literal. Variants are semantic -- `saving`, not `green`.
 */
const planTabVariants = cva(
  'flex-1 flex flex-col items-center gap-0.5 rounded-xl border px-3 py-2.5 text-body font-semibold shadow-sm transition-all data-[state=active]:shadow-none',
  {
    variants: {
      emphasis: {
        saving:
          'border-border-success bg-surface-success text-text-success data-[state=active]:border-fill-success data-[state=active]:bg-fill-success data-[state=active]:text-text-on-dark',
        standard:
          'border-border-default bg-surface-page text-text-secondary data-[state=active]:border-action-primary-hover data-[state=active]:bg-action-primary data-[state=active]:text-text-on-brand',
      },
    },
    defaultVariants: { emphasis: 'standard' },
  },
);

const ResultsDisplay = ({
  cart,
  data,
  handleDownload,
  handleEmail,
  exportAction,
}: {
  cart: types.Cart;
  data: types.OptimizationDataSet;
  handleDownload: (exportData: types.ExportData, planName: string) => Promise<void>;
  handleEmail: (exportData: types.ExportData, planName: string) => Promise<void>;
  exportAction: types.ExportAction | null;
}) => {
  if (
    !data ||
    (!data.best_single_company &&
      (!data.optimization_results || data.optimization_results.length === 0))
  ) {
    return (
      <p className="mt-4 text-text-muted">No optimization results available for this selection.</p>
    );
  }

  let singleCompanyBaselineCost = 0;
  let singleCompanySavings = 0;

  if (data.best_single_company && cart) {
    const singleCompanyProducts = new Set<string>();
    const plan = data.best_single_company.shopping_plan;
    for (const companyName in plan) {
      plan[companyName].items.forEach((item) => {
        singleCompanyProducts.add(
          `${item.product_name}|${item.brand || 'null'}|${item.size || ''}`,
        );
      });
    }
    singleCompanyBaselineCost = cart.items.reduce((total, cartItem) => {
      const id = `${cartItem.product.name}|${cartItem.product.brand_name || 'null'}|${cartItem.product.size || ''}`;
      if (singleCompanyProducts.has(id) && cartItem.baseline_price) {
        return total + cartItem.baseline_price * cartItem.quantity;
      }
      return total;
    }, 0);
    singleCompanySavings =
      singleCompanyBaselineCost > 0
        ? singleCompanyBaselineCost - data.best_single_company.optimized_cost
        : 0;
  }

  const defaultTab = data.best_single_company
    ? 'tab-1'
    : data.optimization_results.length > 0
      ? `tab-${data.optimization_results[0].max_companies}`
      : '';

  const highestSavingResult = data.optimization_results.reduce(
    (max, current) => {
      if (!max || current.savings > max.savings) return current;
      return max;
    },
    null as types.OptimizationResult | null,
  );

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border-default bg-surface-muted px-5 py-4 flex flex-wrap items-center gap-x-6 gap-y-1">
        <span className="text-body text-text-muted">Baseline cost (average across companies)</span>
        <span className="font-bold text-text-primary text-lead">
          ${data.baseline_cost.toFixed(2)}
        </span>
      </div>

      <Tabs defaultValue={defaultTab} className="w-full">
        <TabsList className="flex h-auto w-full gap-1.5 bg-transparent p-0 flex-wrap">
          {data.best_single_company && (
            <TabsTrigger value="tab-1" className={planTabVariants({ className: 'min-w-[120px]' })}>
              <span>Best Single Company</span>
              <span className="text-caption font-normal opacity-70">
                {data.best_single_company.items_found_count}/
                {data.best_single_company.total_items_in_cart} items
              </span>
            </TabsTrigger>
          )}
          {data.optimization_results.map((result) => {
            const percentage =
              data.baseline_cost > 0 ? Math.round((result.savings / data.baseline_cost) * 100) : 0;
            const isHighestSaving =
              highestSavingResult && result.max_companies === highestSavingResult.max_companies;
            return (
              <TabsTrigger
                key={result.max_companies}
                value={`tab-${result.max_companies}`}
                className={planTabVariants({
                  emphasis: isHighestSaving ? 'saving' : 'standard',
                  className: 'min-w-[100px]',
                })}
              >
                <span>{result.max_companies} Companies</span>
                <span className="text-label font-bold">
                  {percentage > 0 ? `Save ${percentage}%` : '-'}
                </span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {data.best_single_company && (
          <TabsContent value="tab-1" className="mt-4">
            <div className="rounded-xl border border-border-default bg-surface-page shadow-sm overflow-hidden">
              <div className="p-5 border-b border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-8">
                  <div>
                    <p className="text-label text-text-subtle uppercase tracking-wide mb-0.5">
                      Total Cost
                    </p>
                    <p className="text-title-sm font-bold text-text-primary">
                      ${data.best_single_company.optimized_cost.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-label text-text-subtle uppercase tracking-wide mb-0.5">
                      You Save
                    </p>
                    <p className="text-title-sm font-bold text-text-success">
                      ${singleCompanySavings.toFixed(2)}
                    </p>
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <ExportButtons
                    exportAction={exportAction}
                    planKey="best-single-company"
                    onEmail={() =>
                      handleEmail(
                        {
                          shopping_plan: data.best_single_company!.shopping_plan,
                          baseline_cost: singleCompanyBaselineCost,
                          optimized_cost: data.best_single_company!.optimized_cost,
                          savings: singleCompanySavings,
                        },
                        'best-single-company',
                      )
                    }
                    onDownload={() =>
                      handleDownload(
                        {
                          shopping_plan: data.best_single_company!.shopping_plan,
                          baseline_cost: singleCompanyBaselineCost,
                          optimized_cost: data.best_single_company!.optimized_cost,
                          savings: singleCompanySavings,
                        },
                        'best-single-company',
                      )
                    }
                  />
                  <p className="text-caption text-text-subtle">
                    Found {data.best_single_company.items_found_count} of{' '}
                    {data.best_single_company.total_items_in_cart} items
                  </p>
                </div>
              </div>
              <PlanDetails plan={data.best_single_company.shopping_plan} />
            </div>
          </TabsContent>
        )}

        {data.optimization_results.map((result) => (
          <TabsContent
            key={result.max_companies}
            value={`tab-${result.max_companies}`}
            className="mt-4"
          >
            <div className="rounded-xl border border-border-default bg-surface-page shadow-sm overflow-hidden">
              <div className="p-5 border-b border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-8">
                  <div>
                    <p className="text-label text-text-subtle uppercase tracking-wide mb-0.5">
                      Total Cost
                    </p>
                    <p className="text-title-sm font-bold text-text-primary">
                      ${result.optimized_cost.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-label text-text-subtle uppercase tracking-wide mb-0.5">
                      You Save
                    </p>
                    <p className="text-title-sm font-bold text-text-success">
                      ${result.savings.toFixed(2)}
                    </p>
                  </div>
                </div>
                <ExportButtons
                  exportAction={exportAction}
                  planKey={`companies-${result.max_companies}`}
                  onEmail={() =>
                    handleEmail(
                      {
                        shopping_plan: result.shopping_plan,
                        baseline_cost: data.baseline_cost,
                        optimized_cost: result.optimized_cost,
                        savings: result.savings,
                      },
                      `companies-${result.max_companies}`,
                    )
                  }
                  onDownload={() =>
                    handleDownload(
                      {
                        shopping_plan: result.shopping_plan,
                        baseline_cost: data.baseline_cost,
                        optimized_cost: result.optimized_cost,
                        savings: result.savings,
                      },
                      `companies-${result.max_companies}`,
                    )
                  }
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
