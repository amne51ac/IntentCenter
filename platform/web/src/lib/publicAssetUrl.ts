/** Resolve `public/` filenames for Vite `base` (e.g. `/app/`). */
export function publicAssetUrl(path: string): string {
  const base = import.meta.env.BASE_URL;
  const p = path.startsWith("/") ? path.slice(1) : path;
  return `${base}${p}`;
}
