import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from './ui/button';
import { cn } from '../lib/utils';
import type { NextButtonProps } from '../types/NextButtonProps';

const NextButton: React.FC<NextButtonProps> = ({ onAfterNavigate, className }) => {
  const router = useRouter();

  // this should user item.substitutions to determine where to go next it should use the page that the user is on.
  const handleNextClick = () => {
    router.push('/substitutions');

    if (onAfterNavigate) {
      onAfterNavigate();
    }
  };

  return (
    <Button onClick={handleNextClick} className={cn("bg-green-500 hover:bg-green-600", className)}>
      Next
    </Button>
  );
};

export default NextButton;
