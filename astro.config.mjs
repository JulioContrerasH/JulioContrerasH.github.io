import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://juliocontrerash.github.io',
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es'],
    routing: { prefixDefaultLocale: false },
  },
  build: {
    format: 'directory',
  },
  devToolbar: {
    enabled: false,
  },
});
