import { apiGet } from '../core/api.js';

export default function homeCategories() {
  return {
    categories: [],
    loading: true,

    async init() {
      // DRF может вернуть либо массив, либо объект { results:[...] }
      const raw = await apiGet('/api/categories/');
      this.categories = Array.isArray(raw) ? raw : raw.results ?? [];
      this.loading    = false;
    },

    col(n) {                      // n = 0 | 1 | 2
      return this.categories.filter((_, i) => i % 3 === n);
    },
  };
}