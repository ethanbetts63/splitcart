import React, { useState } from 'react';
import SearchSourcer from './SearchSourcer';

const ScrollerManager = ({ scrollers, nearbyStoreIds }) => {
  const [loadedCount, setLoadedCount] = useState(0);

  const handleLoadComplete = () => {
    setLoadedCount(prevCount => prevCount + 1);
  };

  if (!scrollers || scrollers.length === 0) {
    return null;
  }

  const renderScroller = (scroller, onLoad) => {
    return (
      <SearchSourcer
        key={scroller.title}
        title={scroller.title}
        searchTerm={scroller.searchTerm}
        sourceUrl={scroller.sourceUrl}
        nearbyStoreIds={nearbyStoreIds}
        seeMoreLink={scroller.seeMoreLink} // Pass the seeMoreLink
        onLoadComplete={onLoad}
      />
    );
  };

  // Once all are loaded, render them without the callback to avoid unnecessary re-renders.
  if (loadedCount >= scrollers.length) {
    return (
      <>
        {scrollers.map((scroller) => renderScroller(scroller, undefined))}
      </>
    );
  }

  // Render one more scroller than has been loaded.
  const scrollersToRender = scrollers.slice(0, loadedCount + 1);

  return (
    <>
      {scrollersToRender.map((scroller, index) => {
        const onLoad = index === loadedCount ? handleLoadComplete : undefined;
        return renderScroller(scroller, onLoad);
      })}
    </>
  );
};

export default ScrollerManager;
