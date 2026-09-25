import type { PriceComparisonChartProps } from '../types/PriceComparisonChartProps';
import { cn } from '@/lib/utils';

const PriceComparisonChart = ({ comparison, categoryName }: PriceComparisonChartProps) => {
  const {
    company_a_name,
    company_b_name,
    cheaper_at_a_percentage,
    cheaper_at_b_percentage,
    same_price_percentage,
    overlap_count,
  } = comparison;

  // Complete class strings keyed by company, never assembled from fragments:
  // Tailwind reads source as text and generates nothing for `bg-${x}`.
  // These are the three chains' own brand colours and carry no good/bad axis,
  // so they come from the --category-* family rather than the feedback one.
  const companyColorMap: { [key: string]: string } = {
    Woolworths: 'bg-category-woolworths',
    Coles: 'bg-category-coles',
    Aldi: 'bg-category-aldi',
  };

  const titleVerb = categoryName.endsWith('s') ? 'Are' : 'Is';
  const title = `${titleVerb} ${categoryName} cheaper at ${company_a_name} or ${company_b_name}?`;

  const sentenceVerb = categoryName.endsWith('s') ? 'were' : 'was';
  let summarySentence;
  if (cheaper_at_a_percentage > cheaper_at_b_percentage) {
    summarySentence = (
      <>
        <span className="font-bold bg-action-primary px-0.5 rounded">
          {cheaper_at_a_percentage}%
        </span>{' '}
        of {categoryName} tested {sentenceVerb} cheaper at{' '}
        <span className="font-bold">{company_a_name}</span> than {company_b_name}.
      </>
    );
  } else if (cheaper_at_b_percentage > cheaper_at_a_percentage) {
    summarySentence = (
      <>
        <span className="font-bold bg-action-primary px-0.5 rounded">
          {cheaper_at_b_percentage}%
        </span>{' '}
        of {categoryName} tested {sentenceVerb} cheaper at{' '}
        <span className="font-bold">{company_b_name}</span> than {company_a_name}.
      </>
    );
  } else {
    summarySentence = (
      <>
        Prices for <span className="font-bold">{categoryName}</span> were competitive between{' '}
        {company_a_name} and {company_b_name}.
      </>
    );
  }

  const segments = [
    {
      percentage: cheaper_at_a_percentage,
      color: companyColorMap[company_a_name] || 'bg-category-other',
      textColor: 'text-text-on-dark',
      label: company_a_name,
    },
    {
      percentage: same_price_percentage,
      color: 'bg-category-neutral',
      textColor: 'text-text-muted',
      label: 'Same Price',
    },
    {
      percentage: cheaper_at_b_percentage,
      color: companyColorMap[company_b_name] || 'bg-category-other',
      textColor: 'text-text-on-dark',
      label: company_b_name,
    },
  ];

  return (
    <div className="rounded-xl border border-border-default bg-surface-page shadow-sm p-5 w-full h-full flex flex-col gap-4">
      {/* Header */}
      <div>
        <h3 className="font-bold text-text-primary text-body leading-snug">{title}</h3>
        <p className="text-body text-text-secondary mt-2 leading-snug">{summarySentence}</p>
        <p className="text-caption text-text-subtle mt-1.5">
          {overlap_count} common products compared
        </p>
      </div>

      {/* Bar */}
      <div className="h-10 w-full rounded-xl overflow-hidden flex bg-surface-sunken">
        {segments.map((segment, index) =>
          segment.percentage > 0 ? (
            <div
              key={index}
              className={cn(
                segment.color,
                'flex items-center justify-center transition-all duration-500',
              )}
              style={{ width: `${segment.percentage}%` }}
              title={`${segment.label}: ${segment.percentage}%`}
            >
              {segment.percentage >= 10 && (
                <span className={cn('text-label font-bold select-none', segment.textColor)}>
                  {segment.percentage}%
                </span>
              )}
            </div>
          ) : null,
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-2">
        {segments.map((segment, index) => (
          <div key={index} className="flex items-center gap-1.5 text-body">
            <span
              className={cn(
                'h-2.5 w-2.5 rounded-full flex-shrink-0 border border-border-default',
                segment.color,
              )}
            />
            <span className="text-text-muted">{segment.label}</span>
            <span className="font-bold text-text-primary">{segment.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PriceComparisonChart;
