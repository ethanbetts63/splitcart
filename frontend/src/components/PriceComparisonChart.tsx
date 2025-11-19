import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import type { PriceComparison } from '../types';

interface PriceComparisonChartProps {
  comparison: PriceComparison;
}

const PriceComparisonChart: React.FC<PriceComparisonChartProps> = ({ comparison }) => {
  const {
    company_a_name,
    company_b_name,
    cheaper_at_a_percentage,
    cheaper_at_b_percentage,
    same_price_percentage,
    overlap_count
  } = comparison;

  const segments = [
    { percentage: cheaper_at_a_percentage, color: 'bg-blue-500', label: company_a_name },
    { percentage: same_price_percentage, color: 'bg-gray-400', label: 'Same Price' },
    { percentage: cheaper_at_b_percentage, color: 'bg-green-500', label: company_b_name },
  ];

  return (
    <Card className="w-full max-w-2xl mx-auto my-4">
      <CardHeader>
        <CardTitle className="text-lg">
          {company_a_name} vs. {company_b_name}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{overlap_count} common products compared</p>
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
