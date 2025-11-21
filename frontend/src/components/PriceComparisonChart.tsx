import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
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

  // Define the mapping of company names to Tailwind CSS color classes
  const companyColorMap: { [key: string]: string } = {
    'Woolworths': 'bg-green-500',
    'Coles': 'bg-red-500',
    'Aldi': 'bg-black',
    'IGA': 'bg-black',
  };

  // Determine if the verb should be "Is" or "Are" for the title
  const titleVerb = categoryName.endsWith('s') ? 'Are' : 'Is';
  const title = `${titleVerb} ${categoryName} cheaper at ${company_a_name} or ${company_b_name}?`;

  // Generate the summary sentence
  const sentenceVerb = categoryName.endsWith('s') ? 'were' : 'was';
  let summarySentence;
  if (cheaper_at_a_percentage > cheaper_at_b_percentage) {
    summarySentence = (
      <>
        <span className="font-bold">{cheaper_at_a_percentage}%</span> of {categoryName} tested {sentenceVerb} cheaper at <span className="font-bold">{company_a_name}</span> than {company_b_name}.
      </>
    );
  } else if (cheaper_at_b_percentage > cheaper_at_a_percentage) {
    summarySentence = (
      <>
        <span className="font-bold">{cheaper_at_b_percentage}%</span> of {categoryName} tested {sentenceVerb} cheaper at <span className="font-bold">{company_b_name}</span> than {company_a_name}.
      </>
    );
  } else {
    summarySentence = (
      <>
        Prices for <span className="font-bold">{categoryName}</span> were competitive between {company_a_name} and {company_b_name}.
      </>
    );
  }

  // Dynamically build the segments array with correct colors
  const segments = [
    {
      percentage: cheaper_at_a_percentage,
      color: companyColorMap[company_a_name] || 'bg-gray-700', // Fallback color
      label: company_a_name
    },
    {
      percentage: same_price_percentage,
      color: 'bg-gray-400',
      label: 'Same Price'
    },
    {
      percentage: cheaper_at_b_percentage,
      color: companyColorMap[company_b_name] || 'bg-gray-800', // Fallback color
      label: company_b_name
    }
  ];

  return (
    <Card className="w-full h-full">
      <CardHeader>
        <CardTitle className="text-lg">
          {title}
        </CardTitle>
        <p className="text-base text-gray-700 mt-1">{summarySentence}</p>
        <p className="text-sm text-muted-foreground pt-2">{overlap_count} common products compared</p>
      </CardHeader>
      <CardContent>
        <div className="w-full">
          {/* Bar */}
          <div className="flex h-8 w-full rounded-md overflow-hidden">
            {segments.map((segment, index) => (
              segment.percentage > 0 && (
                <div
                  key={index}
                  className={`${segment.color} transition-all duration-300`}
                  style={{ width: `${segment.percentage}%` }}
                  title={`${segment.label}: ${segment.percentage}%`}
                />
              )
            ))}
          </div>

          {/* Legend */}
          <div className="mt-4 flex justify-center space-x-4 text-sm">
            {segments.map((segment, index) => (
              <div key={index} className="flex items-center">
                <span className={`h-4 w-4 mr-2 rounded-sm ${segment.color}`} />
                <span>{segment.label}: {segment.percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PriceComparisonChart;
