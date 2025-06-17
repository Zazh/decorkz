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
        console.log('Инициализация компонента product, slug:', this.slug);
        this.item = await apiGet(`/api/products/${this.slug}/`);
        console.log('Текущий товар загружен:', {
          id: this.item.id,
          title: this.item.title,
          category: this.item.category,
          images: this.item.images
        });
        
        this.currentImage =
          this.item.images.find(i => i.is_main) || this.item.images[0] || {};
        console.log('Текущее изображение:', this.currentImage);
        
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
      console.log('Загрузка похожих товаров для категории:', catSlug);
      
      if (!catSlug) {
        console.warn('Нет slug категории для загрузки похожих товаров');
        return;
      }

      try {
        // Получаем все товары из категории
        const data = await apiGet('/api/products/', {
          category__slug: catSlug,
          page_size: 100 // Увеличиваем размер страницы, чтобы получить больше товаров
        });
        console.log('Получены данные от API:', {
          isArray: Array.isArray(data),
          hasResults: data.results !== undefined,
          totalCount: data.count,
          data: data
        });

        // Проверяем формат ответа
        const products = Array.isArray(data) ? data : (data.results || []);
        console.log('Обработанные товары:', products.map(p => ({
          id: p.id,
          title: p.title,
          category: p.category
        })));
        
        // Если товаров мало, показываем все кроме текущего
        if (products.length <= 10) {
          this.related = products.filter(p => p.id !== this.item.id);
        } else {
          const filteredProducts = products.filter(p => p.id !== this.item.id);
          const shuffled = filteredProducts.sort(() => 0.5 - Math.random());
          this.related = shuffled.slice(0, 10);
        }
        
        console.log('Финальный список похожих товаров:', this.related.map(p => ({
          id: p.id,
          title: p.title
        })));
      } catch (e) {
        console.error('Ошибка при загрузке похожих товаров:', e);
        this.related = [];
      }
    },

    formatPrice(price) {
  if (price === undefined || price === null) return '—';
  // Преобразует 10000.00 → 10 000 ₸
  return `${Number(price).toLocaleString('ru-RU')} ₸`;
},

  };
}