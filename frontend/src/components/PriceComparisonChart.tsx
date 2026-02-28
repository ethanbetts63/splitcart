import React from 'react';
import type { PriceComparison } from '../types';

interface PriceComparisonChartProps {
  comparison: PriceComparison;
  categoryName: string;
}

const PriceComparisonChart: React.FC<PriceComparisonChartProps> = ({ comparison, categoryName }) => {
  const {
    company_a_name,
    company_b_name,
    cheaper_at_a_percentage,
    cheaper_at_b_percentage,
    same_price_percentage,
    overlap_count
  } = comparison;

  const companyColorMap: { [key: string]: string } = {
    'Woolworths': 'bg-green-500',
    'Coles': 'bg-red-500',
    'Aldi': 'bg-blue-500',
    'IGA': 'bg-gray-900',
  };

  const titleVerb = categoryName.endsWith('s') ? 'Are' : 'Is';
  const title = `${titleVerb} ${categoryName} cheaper at ${company_a_name} or ${company_b_name}?`;

  const sentenceVerb = categoryName.endsWith('s') ? 'were' : 'was';
  let summarySentence;
  if (cheaper_at_a_percentage > cheaper_at_b_percentage) {
    summarySentence = (
      <>
        <span className="font-bold bg-yellow-300 px-0.5 rounded">{cheaper_at_a_percentage}%</span> of {categoryName} tested {sentenceVerb} cheaper at <span className="font-bold">{company_a_name}</span> than {company_b_name}.
      </>
    );
  } else if (cheaper_at_b_percentage > cheaper_at_a_percentage) {
    summarySentence = (
      <>
        <span className="font-bold bg-yellow-300 px-0.5 rounded">{cheaper_at_b_percentage}%</span> of {categoryName} tested {sentenceVerb} cheaper at <span className="font-bold">{company_b_name}</span> than {company_a_name}.
      </>
    );
  } else {
    summarySentence = (
      <>
        Prices for <span className="font-bold">{categoryName}</span> were competitive between {company_a_name} and {company_b_name}.
      </>
    );
  }

  const segments = [
    {
      percentage: cheaper_at_a_percentage,
      color: companyColorMap[company_a_name] || 'bg-gray-700',
      textColor: 'text-white',
      label: company_a_name,
    },
    {
      percentage: same_price_percentage,
      color: 'bg-gray-200',
      textColor: 'text-gray-500',
      label: 'Same Price',
    },
    {
      percentage: cheaper_at_b_percentage,
      color: companyColorMap[company_b_name] || 'bg-gray-800',
      textColor: 'text-white',
      label: company_b_name,
    },
  ];

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-5 w-full h-full flex flex-col gap-4">
      {/* Header */}
      <div>
        <h3 className="font-bold text-gray-900 text-base leading-snug">{title}</h3>
        <p className="text-sm text-gray-600 mt-2 leading-snug">{summarySentence}</p>
        <p className="text-xs text-gray-400 mt-1.5">{overlap_count} common products compared</p>
      </div>

      {/* Bar */}
      <div className="h-10 w-full rounded-xl overflow-hidden flex bg-gray-100">
        {segments.map((segment, index) =>
          segment.percentage > 0 ? (
            <div
              key={index}
              className={`${segment.color} flex items-center justify-center transition-all duration-500`}
              style={{ width: `${segment.percentage}%` }}
              title={`${segment.label}: ${segment.percentage}%`}
            >
              {segment.percentage >= 10 && (
                <span className={`text-xs font-bold select-none ${segment.textColor}`}>
                  {segment.percentage}%
                </span>
              )}
            </div>
          ) : null
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-2">
        {segments.map((segment, index) => (
          <div key={index} className="flex items-center gap-1.5 text-sm">
            <span className={`h-2.5 w-2.5 rounded-full flex-shrink-0 ${segment.color} border border-gray-200`} />
            <span className="text-gray-500">{segment.label}</span>
            <span className="font-bold text-gray-900">{segment.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PriceComparisonChart;
