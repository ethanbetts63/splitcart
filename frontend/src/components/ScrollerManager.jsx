import React from 'react';
import SearchSourcer from './SearchSourcer';

const ScrollerManager = ({ scrollers, nearbyStoreIds, isLocationLoaded }) => {
  if (!scrollers || scrollers.length === 0) {
    return null;
  }

  // Render all scrollers at once. The loading state is now handled inside each scroller.
  return (
    <>
      {scrollers.map((scroller) => (
        <SearchSourcer
          key={scroller.title}
          title={scroller.title}
          searchTerm={scroller.searchTerm}
          sourceUrl={scroller.sourceUrl}
          nearbyStoreIds={nearbyStoreIds}
          seeMoreLink={scroller.seeMoreLink}
          isLocationLoaded={isLocationLoaded}
        />
      ))}
    </>
  );
};

export default ScrollerManager;
