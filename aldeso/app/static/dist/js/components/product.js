/* static/js/components/product.js */
import { apiGet } from '../core/api.js';

export default function product () {
  return {
    /* ───────── состояние ───────── */
    slug:   window.location.pathname.split('/').filter(Boolean).pop(),
    item:   { category: { slug: '', title: '' }, images: [], attributes: [] },
    related: [],
    currentImage: {},
    loading: true,

    /* ───────── computed ───────── */
    attrValues (name) {
      /* собираем ВСЕ значения по атрибуту name (регистр игнорируем) */
      return (this.item.attributes || [])
        .filter(a => a.attribute.toLowerCase() === name.toLowerCase())
        .map   (a => a.value);
    },
    get heightText  ()  { return this.attrValues('высота').join(', ');  },
    get widthText   ()  { return this.attrValues('длина').join(', '); },
    get sizeText    ()  { return this.attrValues('ширина').join(', '); },

    /* ───────── lifecycle ───────── */
    async init () {
      try {
        this.item = await apiGet(`/api/products/${this.slug}/`);
        this.currentImage =
          this.item.images.find(i => i.is_main) || this.item.images[0] || {};
        // document.title = this.item.title;
        await this.loadRelated();
      } catch (e) {
        console.error('Не удалось загрузить товар', e);
      } finally {
        this.loading = false;
      }
    },

    /* ───────── методы ───────── */
    async loadRelated () {
      const catSlug = this.item.category?.slug;
      if (!catSlug) return;

      const data = await apiGet('/api/products/', {
        category__slug: catSlug,
        page_size: 6
      });

      const list = (data.results ?? data).filter(p => p.id !== this.item.id);
      this.related = list.slice(0, 4);
    },
  };
}