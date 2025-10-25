import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";

const SkeletonProductTile = () => {
  return (
    <Card className="w-full flex flex-col h-full overflow-hidden gap-3">
      <Skeleton className="aspect-square w-full" />
      <CardHeader className="p-0 pb-0 flex flex-col items-center">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </CardHeader>
      <CardContent className="flex-grow p-0 flex justify-center">
        <Skeleton className="h-8 w-1/3" />
      </CardContent>
      <CardFooter className="flex justify-center p-4 pt-0">
        <Skeleton className="h-10 w-full" />
      </CardFooter>
    </Card>
  );
};

export default SkeletonProductTile;
