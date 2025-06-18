import { apiGet } from '../core/api.js';

export default function homeCategories() {
  return {
    categories: [],
    loading: true,

    async init() {
      // DRF может вернуть либо массив, либо объект { results:[...] }
      const raw = await apiGet('/api/categories/', { "parent__isnull": true });
      this.categories = Array.isArray(raw) ? raw : raw.results ?? [];
      this.categories = this.categories.filter(cat => cat.parent_id === null);
      this.loading = false;
    },

    categories: [],
  };
}

