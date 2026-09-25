import { Card, CardContent, CardHeader, CardTitle } from '@/components/common/card';

const ContactDetails = () => {
  return (
    <div className="site-shell py-section">
      <Card className="bg-surface-page text-text-primary border-0 shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center text-title-sm">
            The Splitcart Elavator Pitch:
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4">
            Splitcart is an Australian smart grocery price comparison platform that finds the
            absolute cheapest way to buy your entire shopping list by intelligently splitting it
            across multiple supermarkets. Instead of just comparing single-store totals, it accounts
            for real item-level price differences, delivery fees, store availability, distance, and
            user constraints (like max stores or minimum savings), while also suggesting cheaper
            substitute products you approve. Under the hood, it cleans and normalizes messy
            supermarket data, matches equivalent products across brands and stores, and runs an
            optimization algorithm to surface the best combination—saving users real money without
            the manual tab-hopping. It’s built for budget-conscious shoppers who want clear,
            actionable savings, and for scale, it opens the door to insights like national average
            prices, true discount tracking, and where groceries are genuinely cheaper.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ContactDetails;
