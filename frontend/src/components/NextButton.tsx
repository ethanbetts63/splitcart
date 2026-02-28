import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { cn } from '../lib/utils';
import type { NextButtonProps } from '../types/NextButtonProps';

const NextButton: React.FC<NextButtonProps> = ({ onAfterNavigate, className }) => {
  const navigate = useNavigate();

  // this should user item.substitutions to determine where to go next it should use the page that the user is on.
  const handleNextClick = () => {
    navigate('/substitutions');

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