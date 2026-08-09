import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'overview',
    {
      type: 'category',
      label: 'For pharmacy professionals',
      items: [
        'usage/quickstart',
        'usage/reading-changes',
        'usage/limitations',
        'usage/troubleshooting',
      ],
    },
    {
      type: 'category',
      label: 'For developers',
      items: [
        'technical-details/architecture',
        'technical-details/source-format',
        'technical-details/normalization-and-diffs',
        'technical-details/data-schema',
        'technical-details/provenance-and-validation',
        'reference/cli',
        'operations/monthly-update',
      ],
    },
    {
      type: 'category',
      label: 'About',
      items: ['about/license'],
    },
  ],
};

export default sidebars;
