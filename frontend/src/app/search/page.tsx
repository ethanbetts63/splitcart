import SearchResultsPage from "@/page_components/SearchResultsPage";
import { noindexMetadata } from "@/lib/seo";

export const dynamic = "force-dynamic";
export const metadata = noindexMetadata;

export default function Page() {
  return <SearchResultsPage />;
}
