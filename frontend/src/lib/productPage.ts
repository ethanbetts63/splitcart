import type { Product } from '@/types';

/**
 * The words a product page says about its prices, built once so the `<title>`,
 * the meta description and the visible summary cannot disagree.
 *
 * Every figure is the scraped price with the date it was scraped beside it.
 * seo-standard.md section 0 forbids an undated price claim, and the category
 * FAQs were rewritten on 2026-09-25 for exactly that.
 */

const DATE_FORMAT = new Intl.DateTimeFormat('en-AU', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
});

/** `2026-10-03` → `3 Oct 2026`. Read as UTC so the day never shifts. */
function formatDate(iso: string): string {
  return DATE_FORMAT.format(new Date(`${iso}T00:00:00Z`));
}

function money(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

/** The product as a shopper would name it: name, then size when there is one. */
export function productLabel(product: Product): string {
  return product.size ? `${product.name} ${product.size}` : product.name;
}

/** `Coles vs Woolworths`, in the order the API sorted them (cheapest first). */
function chains(product: Product): string {
  return product.prices.map((price) => price.company).join(' vs ');
}

export function productTitle(product: Product): string {
  return product.prices.length > 1
    ? `${productLabel(product)}: ${chains(product)} price`
    : `${productLabel(product)} price at ${chains(product)}`;
}

/**
 * Which store is cheapest and by how much, or that the stores agree.
 * `null` when there is nothing to compare.
 */
export function priceSummary(product: Product): string | null {
  const prices = product.prices.map((price) => ({
    company: price.company,
    amount: Number.parseFloat(price.price_display),
  }));
  if (prices.length < 2) return null;

  const [cheapest, ...rest] = prices;
  const dearest = rest[rest.length - 1];
  if (dearest.amount === cheapest.amount) {
    return `The same price at ${prices.map((price) => price.company).join(' and ')}: ${money(cheapest.amount)}.`;
  }
  return (
    `Cheapest at ${cheapest.company}: ${money(cheapest.amount)}, ` +
    `${money(dearest.amount - cheapest.amount)} less than ${dearest.company}.`
  );
}

/** `Prices checked 3 Oct 2026`, or the span when the stores were scraped on different days. */
export function pricesChecked(product: Product): string | null {
  const dates = product.prices
    .map((price) => price.scraped_date)
    .filter((date): date is string => Boolean(date))
    .sort();
  if (!dates.length) return null;
  const first = dates[0];
  const last = dates[dates.length - 1];
  return first === last
    ? `Prices checked ${formatDate(first)}`
    : `Prices checked between ${formatDate(first)} and ${formatDate(last)}`;
}

export function productDescription(product: Product): string {
  const listed = product.prices
    .map((price) => `${price.company} $${price.price_display}`)
    .join(', ');
  return [`${productLabel(product)}: ${listed}.`, priceSummary(product), pricesChecked(product)]
    .filter(Boolean)
    .join(' ')
    .replace(/([^.])$/, '$1.');
}
