import React, { useEffect } from 'react';
import './Background.css';

const Background = () => {
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollPercent = docHeight > 0 ? scrollY / docHeight : 0;

      const angle = scrollPercent * 60;

      const centerX = 50;
      const centerY = 50;
      const radius = 70;

      const pos1x = centerX + radius * Math.cos(angle * (Math.PI / 180));
      const pos1y = centerY + radius * Math.sin(angle * (Math.PI / 180));

      const pos2x = centerX + radius * Math.cos((angle + 90) * (Math.PI / 180));
      const pos2y = centerY + radius * Math.sin((angle + 90) * (Math.PI / 180));

      const pos3x = centerX + radius * Math.cos((angle + 180) * (Math.PI / 180));
      const pos3y = centerY + radius * Math.sin((angle + 180) * (Math.PI / 180));

      const pos4x = centerX + radius * Math.cos((angle + 270) * (Math.PI / 180));
      const pos4y = centerY + radius * Math.sin((angle + 270) * (Math.PI / 180));

      document.documentElement.style.setProperty('--pos1', `${pos1x}% ${pos1y}%`);
      document.documentElement.style.setProperty('--pos2', `${pos2x}% ${pos2y}%`);
      document.documentElement.style.setProperty('--pos3', `${pos3x}% ${pos3y}%`);
      document.documentElement.style.setProperty('--pos4', `${pos4x}% ${pos4y}%`);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return <div className="background-container"></div>;
};

export default Background;