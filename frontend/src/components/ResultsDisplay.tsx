import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download, Mail } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import PlanDetails from '@/components/PlanDetails';
import * as types from '@/types';

const ResultsDisplay = ({ data, handleDownload, handleEmail, exportAction }: { 
    data: types.OptimizationDataSet;
    handleDownload: (exportData: types.ExportData, planName: string) => Promise<void>;
    handleEmail: (exportData: types.ExportData, planName: string) => Promise<void>;
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
    }, null as types.OptimizationResult | null);

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

export default ResultsDisplay;