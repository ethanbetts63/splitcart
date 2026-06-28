export type ShoppingPlan = {
  [companyName: string]: {
    items: {
      product_name: string;
      brand: string | null;
      size: string;
      quantity: number;
      price: number;
      image_url: string | null;
      image_base64?: string;
    }[];
    company_name: string;
    total_cost?: number;
    subtotal?: number;
  };
};
