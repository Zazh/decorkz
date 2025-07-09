import { apiGet } from '../core/api.js';

export default function homeCategories() {
  return {
    categories: [],
    loading: true,

    async init() {
      const raw = await apiGet('/api/categories/');
      const all = Array.isArray(raw) ? raw : raw.results ?? [];
      // Оставляем только главные (root) категории
      this.categories = all.filter(cat => cat.parent_id === null);
      this.loading    = false;
    },

    col(n) {                      // n = 0 | 1 | 2
      return this.categories.filter((_, i) => i % 3 === n);
    },
  };
}
