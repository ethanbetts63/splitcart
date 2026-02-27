export const FounderLetterSection = () => {
  return (
    <div className="container mx-auto px-4 md:px-16 pt-1 pb-1">
      <div className="text-center mb-8">
        <h2 className="text-5xl font-bold tracking-tight text-gray-900 max-w-2xl mx-auto">
          What percentage of a whole chicken is bone weight?
        </h2>
        <p className="text-xl mt-4">Short answer: <span className="font-bold">25-32%</span>. Most common answer: <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Who cares?</span></p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-12 text-lg ">
        <div className="flex flex-col gap-4">
          <p>
            <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">I care.</span> And if you're like me then you care too. If you're like me, you've considered the dollar value of a rewards point. Or weighed the merits of ply count versus the per kilo price of toilet paper.
          </p>
          <p className="font-bold">
            If you're like me then SplitCart was built for you. I know this to be a fact because I built SplitCart for me.
          </p>
          <p>
            The idea is simple. Why not buy each item in my shopping list from the store where it's cheapest? Becuase you don't know the price of every item in every store. Becuase you'd never go to ten stores on one shopping run. Becuase it would be a hassle.
          </p>
        </div>
        <div className="flex flex-col gap-4">
          <p>
            I've collected the prices. I've mathematically calculated the best two, three, or four store combinations, and I've removed as much hassle as humanly possible.
          </p>
          <p>
            So, welcome aboard fellow bargain hunter. I hope SplitCart can be as useful to you as it is to me. <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Expect to save 10-15%</span> on your grocery bill!
          </p>
          <p>
            If you have questions, suggestions or anything else I'd love to hear from you.
          </p>
          <div>
            <p>Happy hunting,</p>
            <p className="font-bold"><span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Ethan Betts</span>, <a href="mailto:ethanbetts63@gmail.com" className="text-blue-600 hover:underline">ethanbetts63@gmail.com</a></p>
            <p className="italic text-sm text-gray-600">Founder and Developer</p>
          </div>
        </div>
      </div>
    </div>
  );
};
