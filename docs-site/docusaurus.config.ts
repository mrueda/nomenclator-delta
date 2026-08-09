import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const isProduction = process.env.NODE_ENV === 'production';

const config: Config = {
  title: 'nomenclator-delta Docs',
  tagline: 'Presentation-level change history for Spain\'s Nomenclátor',
  url: 'https://mrueda.github.io',
  baseUrl: '/nomenclator-delta/',
  favicon: 'img/nomenclator-delta-logo.svg',
  organizationName: 'mrueda',
  projectName: 'nomenclator-delta',
  trailingSlash: true,
  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: 'docs',
          showLastUpdateAuthor: false,
          showLastUpdateTime: true,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],
  themes: isProduction
    ? [
        [
          '@easyops-cn/docusaurus-search-local',
          {
            hashed: true,
            language: ['en'],
            indexDocs: true,
            indexBlog: false,
            docsRouteBasePath: '/docs',
            searchResultLimits: 8,
            searchResultContextMaxLength: 50,
          },
        ],
      ]
    : [],
  themeConfig: {
    image: 'img/nomenclator-delta-wordmark.svg',
    metadata: [
      {
        name: 'keywords',
        content: 'Nomenclátor, pharmacy, medicines, Código Nacional, Ministerio de Sanidad, price changes',
      },
    ],
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'nomenclator-delta',
      logo: {
        alt: 'nomenclator-delta logo',
        src: 'img/nomenclator-delta-logo.svg',
      },
      items: [
        {
          href: 'pathname:///app/',
          label: 'Open app',
          position: 'left',
        },
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          to: '/docs/operations/monthly-update',
          label: 'Monthly workflow',
          position: 'left',
        },
        {
          href: 'https://github.com/mrueda/nomenclator-delta',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'For pharmacy professionals',
          items: [
            {
              label: 'Open app',
              href: 'pathname:///app/',
            },
            {
              label: 'Using the app',
              to: '/docs/usage/quickstart',
            },
            {
              label: 'Interpreting changes',
              to: '/docs/usage/reading-changes',
            },
          ],
        },
        {
          title: 'For developers',
          items: [
            {
              label: 'Architecture',
              to: '/docs/technical-details/architecture',
            },
            {
              label: 'Data model',
              to: '/docs/technical-details/data-schema',
            },
            {
              label: 'CLI reference',
              to: '/docs/reference/cli',
            },
          ],
        },
        {
          title: 'Project',
          items: [
            {
              label: 'Source code',
              href: 'https://github.com/mrueda/nomenclator-delta',
            },
            {
              label: 'Official source',
              href: 'https://www.sanidad.gob.es/profesionales/nomenclator.do',
            },
            {
              label: 'License',
              to: '/docs/about/license',
            },
          ],
        },
      ],
      copyright: 'Copyright © 2026 Manuel Rueda. Independent project using Ministerio de Sanidad data.',
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
