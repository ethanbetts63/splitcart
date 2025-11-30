import { Skeleton } from "./ui/skeleton";
import { Card, CardHeader, CardContent, CardFooter } from "./ui/card";

const SkeletonProductTile = () => {
  return (
    <Card className="w-full flex flex-col h-full overflow-hidden">
      <Skeleton className="aspect-square w-full" />
      <CardHeader className="p-0 text-center flex flex-col items-center gap-1 pt-2">
        <Skeleton className="h-12 w-3/4" /> {/* Match h-12 of real title */}
        <Skeleton className="h-4 w-1/2" /> {/* For the brand description */}
      </CardHeader>
      <CardContent className="flex-grow px-3 flex justify-center items-center">
        <Skeleton className="h-6 w-2/3" /> {/* Represents PriceDisplay */}
      </CardContent>
      <CardFooter className="flex justify-center pb-0 px-4">
        <Skeleton className="h-10 w-full" /> {/* Represents AddToCartButton */}
      </CardFooter>
    </Card>
  );
};

export default SkeletonProductTile;
