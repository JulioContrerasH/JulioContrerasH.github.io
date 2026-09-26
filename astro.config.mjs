import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://juliocontrerash.github.io',
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  build: {
    format: 'directory',
  },
  devToolbar: {
    enabled: false,
  },
});
