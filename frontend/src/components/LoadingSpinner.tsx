import React, { useEffect, useState } from 'react';
import { Spinner } from "@/components/ui/spinner";

const loadingMessages = [
  "Making the cart go Split...",
  "Splitting the cart senseless...",
  "The cart never knew what split it...",
  "Split it and quit it...",
  "Hacking capitalism responsibly...",
  "To Split or not to Split that is the question...",
  "\“The definition of insanity is buying everything from one store.\”\n— Albert Einstein (definitely said this)",
  "Teaching the cart to divide and conquer…",
  "Calculating the most peaceful way to start a price war...",
  "Performing complex cart surgery. Please hold...",
  "Splitting hairs. And carts...",
  "Applying advanced algorithms to banana prices...",
  "Sawing the cart in half...",
  "Determining the depth of the cookie jar...",
  "Split happens...",
  "Pondering the philosophical implications of a cheaper onion...",
  "Prioritising chocolate savings over world peace...",
  "No carts were harmed in the making of these savings...",
  "Ambusing high prices...",
  "Staging a hostile takeover of the dairy aisle...",
  "Interrogating the lettuce. It's talking...",
  "Debating if 'artisanal' is really worth the extra $3 on your crackers...",
  "Gaslighting the cash register...",
  "Looking between the couch cushions for spare change...",
  "Hiring one more intern for good measure...",
  "The potatoes have unionized...",
  "Teaching the barcode scanner to love...",
  "Making your cart more aerodynamic...",
  "Translating your shopping list into Dolphin to see if they have better ideas...",
  "Negotiating peace between rival supermarkets...",
  "Optimizing. Strategizing. Slightly judging your shopping list...",
  "\“In the beginning, there was one cart. Then came optimization.\”\n— Genesis of Savings, 3:14",
  "\“Give a man a cart, and he’ll shop for a day. Teach a man to split a cart, and he’ll save for a lifetime.\”\n— Confucius (probably)",
  "\“I came, I saw, I split.\”\n— Julius Caesar",
  "Running a background check on your biscuits...",
  "Balancing taste, price, and your deep emotional attachment to Nutella...",
  "Literally comparing apples to oranges...",
  "Split me baby one more time!",
  "We're gonna need a bigger cart...",
  "That's not a cart, THIS is a cart!",
  "Finding Wally in the discount aisle...",
  "Training squirrels to fetch better deals...",
  "Consulting the shopping cart spirits...",
  "Calculating the optimal number of stores to annoy...",
];

import type { LoadingSpinnerProps } from '../types/LoadingSpinnerProps';

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ fullScreen = true }) => {
  const [loadingMessage, setLoadingMessage] = useState("");

  const selectRandomMessage = () => {
    const randomIndex = Math.floor(Math.random() * loadingMessages.length);
    setLoadingMessage(loadingMessages[randomIndex]);
  };

  useEffect(() => {
    selectRandomMessage(); // Select a random message on initial load
    const interval = setInterval(() => {
      selectRandomMessage();
    }, 7000); // 7 seconds

    return () => clearInterval(interval); // Cleanup on unmount
  }, []);

  if (fullScreen) {
    return (
      <div className="container mx-auto p-4 flex flex-col items-center justify-center text-center" style={{ minHeight: 'calc(100vh - 10rem)' }}>
        <h1 className="text-2xl font-bold mb-4" style={{ whiteSpace: 'pre-line' }}>{loadingMessage}</h1>
        <Spinner /> 
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center text-center p-8">
        <h1 className="text-xl font-bold mb-4" style={{ whiteSpace: 'pre-line' }}>{loadingMessage}</h1>
        <Spinner />
    </div>
  );
};

export default LoadingSpinner;
