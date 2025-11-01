import React from 'react';
import { Badge } from "./ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import fallbackImage from '@/assets/splitcart_symbol_v6.png';

// These imports will need to be adjusted based on where the logos are.
// For now, I'll assume they are in the assets folder.
import aldiLogo from '../assets/ALDI_logo.webp';
import colesLogo from '../assets/coles_logo.webp';
import igaLogo from '../assets/iga_logo.webp';
import woolworthsLogo from '../assets/woolworths_logo.webp';

// This type will need to be imported from where it's defined, or defined here.
// For now, I will define it here.
interface ShoppingPlan {
  [storeName: string]: {
    items: {
      product_name: string;
      brand: string | null;
      size: string;
      quantity: number;
      price: number;
      image_url: string | null;
    }[];
    company_name: string;
    store_address: string;
    total_cost?: number;
  };
}

const companyLogos: { [key: string]: string } = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

const PlanDetails = ({ plan }: { plan: ShoppingPlan }) => (
    <div className="mt-4 space-y-8">
        {Object.entries(plan).filter(([, store_plan]) => store_plan.items && store_plan.items.length > 0).map(([storeName, store_plan]) => {
            const storeTotal = store_plan.items.reduce((acc, item) => acc + (item.price * item.quantity), 0);
            const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
                e.currentTarget.src = fallbackImage;
            };
            const logo = companyLogos[store_plan.company_name];

            return (
                <div key={storeName} className="border rounded-lg p-4 bg-muted/20">
                    <div className="flex items-center justify-center gap-4 mb-2">
                        {logo && <img src={logo} alt={store_plan.company_name} className="h-10 w-auto" />}
                        <h2 className="text-2xl font-bold">{storeName}</h2>
                    </div>
                    <p className="text-center text-sm text-muted-foreground mb-4">{store_plan.store_address}</p>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[100px]">&nbsp;</TableHead>
                                <TableHead className="text-center">Product</TableHead>
                                <TableHead className="text-center">Quantity</TableHead>
                                <TableHead className="text-right">Unit Price</TableHead>
                                <TableHead className="text-right">Total Price</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {store_plan.items.map((item, index) => (
                                <TableRow key={index}>
                                    <TableCell>
                                        <img
                                            src={item.image_url || fallbackImage}
                                            alt={item.product_name}
                                            className="w-16 h-16 object-cover rounded-md"
                                            onError={handleImageError}
                                        />
                                    </TableCell>
                                    <TableCell className="font-medium text-center">
                                        <div>{item.product_name}</div>
                                        {((item.brand && item.brand !== 'N/A') || item.size) ? (
                                            <div className="text-sm text-muted-foreground flex justify-center items-center mt-1">
                                                {item.brand && item.brand !== 'N/A' && <span>{item.brand}</span>}
                                                {item.brand && item.brand !== 'N/A' && item.size && <span className="mx-1">•</span>}
                                                {item.size && <Badge variant="outline">{item.size}</Badge>}
                                            </div>
                                        ) : null}
                                    </TableCell>
                                    <TableCell className="text-center">{item.quantity}</TableCell>
                                    <TableCell className="text-right">${item.price.toFixed(2)}</TableCell>
                                    <TableCell className="text-right">${(item.price * item.quantity).toFixed(2)}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                        <TableFooter>
                            <TableRow>
                                <TableCell colSpan={4}>Total for {storeName}</TableCell>
                                <TableCell className="text-right">${storeTotal.toFixed(2)}</TableCell>
                            </TableRow>
                        </TableFooter>
                    </Table>
                </div>
            )
        })}
    </div>
);

export default PlanDetails;