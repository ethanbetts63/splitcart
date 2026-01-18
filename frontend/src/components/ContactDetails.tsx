import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const ContactDetails: React.FC = () => {
    return (
        <div className="container mx-auto px-4 py-8 ">
            <Card className="bg-white text-black border-0 shadow-md">
                <CardHeader>
                    <CardTitle className="flex items-center text-2xl">
                        The ForeverFlower Elavator Pitch:
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="mb-4">
                        ForeverFlower fills a few niche gaps in the flower market. There are no annual flower subscriptions, there are no options for upfront payment for subscriptions, there are no options for sending flowers far into the future, there are no flower subscriptions built so that you can pass custody over to the person receiving the gift and all flower subscriptions are regionally based. ForeverFlower can operate in any region where flowers can be delivered. It’s a bouquet organizing middle man but by allowing customers to pay upfront we leverage the time value of money to actually decrease the upfront cost and essentially negate our service fee.
                    </p>
                </CardContent>
            </Card>
        </div>
    );
};

export default ContactDetails;
