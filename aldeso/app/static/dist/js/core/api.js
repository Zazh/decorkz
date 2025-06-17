/* API-обёртки и полезные хелперы */
export async function apiGet (path, params = {}) {
  const url = new URL(path, window.location.origin);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);

  const r = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!r.ok) throw new Error(`API error ${ r.status }`);
  return await r.json();
}

/* При желании: кэширование простых GET-ов */
const cache = new Map();
export async function cachedGet (path, params = {}) {
  const key = path + JSON.stringify(params);
  if (cache.has(key)) return cache.get(key);
  const data = await apiGet(path, params);
  cache.set(key, data);
  return data;
}