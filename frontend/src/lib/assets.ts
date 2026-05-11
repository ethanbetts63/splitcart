export type ImageAsset = string | { src: string };

export function assetSrc(asset: ImageAsset): string {
  return typeof asset === "string" ? asset : asset.src;
}

export function assetSrcSet(items: Array<[ImageAsset, number]>): string {
  return items.map(([asset, width]) => `${assetSrc(asset)} ${width}w`).join(", ");
}
