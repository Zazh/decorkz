/* static/js/components/catalog.js */
import { apiGet } from '../core/api.js';

export default function catalog () {
  return {
    /* ───────── состояние ───────── */
    products:   [],
    categories: [],
    loading:    true,

    page:       1,
    perPage:    20,
    totalPages: 1,

    /* H1-заголовок страницы */
    currentTitle: 'Каталог товаров',

    /* выбранные фильтры (меняются из filterModal) */
    filters: {
      price:    null,          // '0-10000', '10000-49999', … | null
      length:   null,          // см. buildParams()
      width:    null,
      height:   null,
      ordering: '-price',      // '', 'title', '-title', 'price', '-price'
    },

    /* ───────── computed ───────── */
    get slug () {       // '' | 'plintusy' | …
      return window.location.pathname
                   .split('/')
                   .filter(Boolean)
                   .pop() || '';
    },

    /** вернуть значение атрибута по имени (длина, ширина, …) */
    getAttr (product, name) {
      const a = product.attributes
                        .find(x => x.attribute.toLowerCase() === name);
      return a ? a.value : null;
    },

    /* ───────── lifecycle ───────── */
    async init () {
      /* 1. категории (нужны для заголовка) */
      try {
        const catResp   = await apiGet('/api/categories/');
        this.categories = Array.isArray(catResp)
                        ? catResp
                        : catResp.results ?? [];

        const cat = this.categories.find(c => c.slug === this.slug);
        if (cat) {
          this.currentTitle = cat.title;
          // document.title    = cat.title;
        }
      } catch (e) { console.error('Не удалось загрузить категории', e); }

      /* 2. товары */
      await this.fetchProducts();
    },

    /* ───────── helpers ───────── */
    /** формируем query-параметры с учётом фильтров */
buildParams () {
  const p = { page: this.page };
  if (this.slug) p['category__slug'] = this.slug;

  /* ─ Цена ─ */
  if (this.filters.price) {
    const [min,max] = this.filters.price.split('-');
    if (min) p['price_min'] = min;
    if (max) p['price_max'] = max;
  }

  /* ─ Габариты ─ */
  const map = { length:'length', width:'width', height:'height' };
  for (const k in map) {
    if (!this.filters[k]) continue;
    const [min,max] = this.filters[k].split('-');
    if (min) p[`${map[k]}_min`] = min;
    if (max) p[`${map[k]}_max`] = max;
  }

  /* ─ Сортировка ─ */
  if (this.filters.ordering) p.ordering = this.filters.ordering;

  return p;
},

    /** загрузка товаров */
    async fetchProducts () {
      this.loading = true;
      try {
        const data = await apiGet('/api/products/', this.buildParams());
        this.products   = data.results ?? data;          // DRF-pagination
        this.totalPages = data.count
                        ? Math.ceil(data.count / this.perPage)
                        : 1;
      } finally { this.loading = false; }
    },

    /* ───────── внешний API ───────── */
    /** вызывается из модалки при «Применить» */
    async applyFilters (obj) {
      this.page    = 1;
      this.filters = { ...this.filters, ...obj };
      await this.fetchProducts();
    },

    /* ───────── раскладка 3-колонки ───────── */
    col (n) {              // 0,1,2
      return this.products.filter((_, i) => i % 3 === n);
    },

    /* ───────── пагинация ───────── */
    nextPage () {
      if (this.page < this.totalPages) {
        this.page++;
        this.fetchProducts();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    },
    prevPage () {
      if (this.page > 1) {
        this.page--;
        this.fetchProducts();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    },
  };
}