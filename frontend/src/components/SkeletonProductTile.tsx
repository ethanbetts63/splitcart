import { Skeleton } from "./ui/skeleton";

const SkeletonProductTile = () => {
  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden w-full h-full">
      <Skeleton className="aspect-square w-full rounded-none" />
      <div className="p-3 flex flex-col gap-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <div className="mt-auto pt-2 border-t border-gray-100 flex items-center justify-between">
          <Skeleton className="h-4 w-1/3" />
          <div className="flex gap-1">
            <Skeleton className="h-5 w-5 rounded-sm" />
            <Skeleton className="h-5 w-5 rounded-sm" />
          </div>
        </div>
        <Skeleton className="h-9 w-full rounded-lg" />
      </div>
    </div>
  );
};

export default SkeletonProductTile;
