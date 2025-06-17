import Alpine from 'https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/module.esm.js';

import catalog        from '../components/catalog.js';
import sidebar        from '../components/sidebar.js';
import homeCategories from '../components/homeCategories.js';
import product        from '../components/product.js';
import searchModal    from '../components/searchModal.js';


Alpine.data('catalog',        catalog);
Alpine.data('sidebar',        sidebar);
Alpine.data('homeCategories', homeCategories);
Alpine.data('product',        product);
Alpine.data('searchModal',    searchModal);

Alpine.start();                                                 // ⬅ запускаем ПОСЛЕ регистрации