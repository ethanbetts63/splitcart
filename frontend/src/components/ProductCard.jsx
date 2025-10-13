import React from 'react';
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import './ProductCard.css';

export function ProductCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Product Name</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="product-card-image-container">
          <p>Image</p>
        </div>
      </CardContent>
      <CardFooter className="product-card-footer">
        <p>$9.99</p>
        <Button>Add to Cart</Button>
      </CardFooter>
    </Card>
  );
}
