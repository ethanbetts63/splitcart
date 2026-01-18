import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const ContactDetails: React.FC = () => {
    return (
        <div className="container mx-auto px-4 py-8 ">
            <Card className="bg-white text-black border-0 shadow-md">
                <CardHeader>
                    <CardTitle className="flex items-center text-2xl">
                        The Splitcart Elavator Pitch:
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="mb-4">
                        Splitcart is a price comparison tool designed to help Australian shoppers save money on their grocery bills. By comparing prices across major supermarkets like Woolworths, Coles, Aldi, and IGA, Splitcart empowers users not just make more informed decisions, but also leverage algorithms to mathematically deduce the lowest possible price strategy for buying their groceries. Although other grocery comparison sites exist, none have thought to use substitutions, which drastically increases the savings potential.
                    </p>
                </CardContent>
            </Card>
        </div>
    );
};

export default ContactDetails;
