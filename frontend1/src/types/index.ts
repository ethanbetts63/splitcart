// --- Data Structures ---
type Store = {
  id: number;
  store_name: string;
  company_name: string;
  latitude: number;
  longitude: number;
};

type MapCenter = {
  latitude: number;
  longitude: number;
  radius: number;
} | null;

export { type Store, type MapCenter };
