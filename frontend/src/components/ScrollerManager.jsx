import React, { useState } from 'react';
import HorizontalProductScroller from './HorizontalProductScroller';

const ScrollerManager = ({ titles }) => {
  const [loadedCount, setLoadedCount] = useState(0);

  const handleLoadComplete = () => {
    setLoadedCount(prevCount => prevCount + 1);
  };

  // Render one more scroller than has been loaded.
  // The last one will have the callback to trigger the next load.
  const scrollersToRender = titles.slice(0, loadedCount + 1);

  if (!titles || titles.length === 0) {
    return null;
  }

  // Ensure we don't try to render more scrollers than exist
  if (loadedCount >= titles.length) {
    return (
      <>
        {titles.map((title) => (
          <HorizontalProductScroller key={title} title={title} />
        ))}
      </>
    );
  }

  return (
    <>
      {scrollersToRender.map((title, index) => (
        <HorizontalProductScroller
          key={title}
          title={title}
          onLoadComplete={index === loadedCount ? handleLoadComplete : undefined}
        />
      ))}
    </>
  );
};

export default ScrollerManager;
