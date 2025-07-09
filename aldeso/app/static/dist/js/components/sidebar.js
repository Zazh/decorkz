import { apiGet } from '../core/api.js';

export default function sidebar() {
  return {
    categories: [],
    mainCategories: [],
    subCategoriesMap: {},

    get activeSlug() {
      return window.location.pathname.split('/').filter(Boolean).pop() || '';
    },

    async init() {
      try {
        const data = await apiGet('/api/categories/');
        const list = Array.isArray(data) ? data : data.results ?? [];

        // Главные (root) категории
        this.mainCategories = list.filter(c => c.parent_id === null);

        // Карта: id главной → список подкатегорий
        this.subCategoriesMap = {};
        this.mainCategories.forEach(main => {
          this.subCategoriesMap[main.id] = list.filter(c => c.parent_id === main.id);
        });

        this.categories = list; // если где-то ещё нужно полный список

      } catch (err) {
        console.error('Не удалось загрузить категории', err);
        this.categories = [];
        this.mainCategories = [];
        this.subCategoriesMap = {};
      }
    },
  };
}
