import React from 'react';
import { Badge } from './common/badge';
import fallbackImage from '@/assets/splitcart_symbol_v6.webp';
import aldiLogo from '../assets/ALDI_logo.webp';
import colesLogo from '../assets/coles_logo.webp';
import woolworthsLogo from '../assets/woolworths_logo.webp';
import type { ShoppingPlan } from '../types/ShoppingPlan';
import { assetSrc } from '@/lib/assets';

const companyLogos: { [key: string]: string } = {
  Aldi: assetSrc(aldiLogo),
  Coles: assetSrc(colesLogo),
  Woolworths: assetSrc(woolworthsLogo),
};

const PlanDetails = ({ plan }: { plan: ShoppingPlan }) => (
  <div className="divide-y divide-border-subtle">
    {Object.entries(plan)
      .filter(([, companyPlan]) => companyPlan.items && companyPlan.items.length > 0)
      .map(([companyName, companyPlan]) => {
        const companyTotal = companyPlan.items.reduce(
          (acc, item) => acc + item.price * item.quantity,
          0,
        );
        const logo = companyLogos[companyPlan.company_name];

        const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
          if (e.currentTarget.src !== assetSrc(fallbackImage)) {
            e.currentTarget.src = assetSrc(fallbackImage);
          }
        };

        return (
          <div key={companyName} className="p-5">
            <div className="flex items-center gap-4 mb-5">
              {logo && (
                <img
                  src={logo}
                  alt={companyPlan.company_name}
                  className="h-10 w-auto flex-shrink-0"
                />
              )}
              <div className="flex-grow min-w-0">
                <h2 className="font-bold text-lead text-text-primary leading-tight">
                  {companyName}
                </h2>
              </div>
              <div className="flex-shrink-0 text-right">
                <p className="text-label text-text-subtle uppercase tracking-wide">Company Total</p>
                <p className="font-bold text-lead text-text-primary">${companyTotal.toFixed(2)}</p>
              </div>
            </div>

            <div className="overflow-x-auto -mx-5 px-5">
              <table className="w-full min-w-[480px] text-body-sm">
                <thead>
                  <tr className="border-b border-border-subtle">
                    <th className="pb-2 w-14" />
                    <th className="pb-2 text-left font-semibold text-text-muted">Product</th>
                    <th className="pb-2 text-center font-semibold text-text-muted w-16">Qty</th>
                    <th className="pb-2 text-right font-semibold text-text-muted w-24">Unit</th>
                    <th className="pb-2 text-right font-semibold text-text-muted w-24">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {companyPlan.items.map((item, index) => (
                    <tr key={index} className="group">
                      <td className="py-3 pr-3">
                        <img
                          src={item.image_url || assetSrc(fallbackImage)}
                          alt={item.product_name}
                          className="w-12 h-12 object-cover rounded-lg border border-border-subtle"
                          onError={handleImageError}
                        />
                      </td>
                      <td className="py-3 pr-3">
                        <p className="font-medium text-text-primary leading-snug">
                          {item.product_name}
                        </p>
                        {((item.brand && item.brand !== 'N/A') || item.size) && (
                          <div className="flex items-center gap-1.5 mt-0.5">
                            {item.brand && item.brand !== 'N/A' && (
                              <span className="text-caption text-text-subtle">{item.brand}</span>
                            )}
                            {item.brand && item.brand !== 'N/A' && item.size && (
                              <span className="text-text-subtle">.</span>
                            )}
                            {item.size && (
                              <Badge variant="outline" className="px-1.5 py-0">
                                {item.size}
                              </Badge>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="py-3 text-center text-text-control font-medium">
                        {item.quantity}
                      </td>
                      <td className="py-3 text-right text-text-control">
                        ${item.price.toFixed(2)}
                      </td>
                      <td className="py-3 text-right font-semibold text-text-primary">
                        ${(item.price * item.quantity).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-border-default">
                    <td colSpan={4} className="pt-3 text-body-sm text-text-muted font-medium">
                      Total for {companyName}
                    </td>
                    <td className="pt-3 text-right font-bold text-text-primary">
                      ${companyTotal.toFixed(2)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        );
      })}
  </div>
);

export default PlanDetails;
