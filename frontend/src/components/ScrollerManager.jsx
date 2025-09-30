import React, { useState } from 'react';
import SearchSourcer from './SearchSourcer';

const ScrollerManager = ({ scrollers }) => {
  const [loadedCount, setLoadedCount] = useState(0);

  const handleLoadComplete = () => {
    setLoadedCount(prevCount => prevCount + 1);
  };

  if (!scrollers || scrollers.length === 0) {
    return null;
  }

  // Render one more scroller than has been loaded.
  const scrollersToRender = scrollers.slice(0, loadedCount + 1);

  // Once all are loaded, render them without the callback to avoid unnecessary re-renders.
  if (loadedCount >= scrollers.length) {
    return (
      <>
        {scrollers.map((scroller) => (
          <SearchSourcer
            key={scroller.title}
            title={scroller.title}
            searchTerm={scroller.searchTerm}
          />
        ))}
      </>
    );
  }

  return (
    <>
      {scrollersToRender.map((scroller, index) => (
        <SearchSourcer
          key={scroller.title}
          title={scroller.title}
          searchTerm={scroller.searchTerm}
          onLoadComplete={index === loadedCount ? handleLoadComplete : undefined}
        />
      ))}
    </>
  );
};

export default ScrollerManager;
