import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import useBaseUrl from '@docusaurus/useBaseUrl';
import styles from './index.module.css';

const userLinks = [
  {
    eyebrow: 'Search',
    title: 'Find a presentation',
    text: 'Search the Spanish app by Código Nacional, medicine name, active ingredient, or laboratory.',
    to: 'pathname:///app/',
  },
  {
    eyebrow: 'Interpret',
    title: 'Understand a change',
    text: 'See what additions, removals, and changed fields mean—and what they do not mean.',
    to: '/docs/usage/reading-changes',
  },
  {
    eyebrow: 'Verify',
    title: 'Check the source',
    text: 'Find the month, source file, checksum, and link to the Ministerio de Sanidad for each result.',
    to: '/docs/usage/quickstart#check-the-source',
  },
];

const developerLinks = [
  {
    eyebrow: 'Pipeline',
    title: 'Add a monthly comparison',
    text: 'Follow automatic monthly updates or recover a missing release using the manual workflow.',
    to: '/docs/operations/monthly-update',
  },
  {
    eyebrow: 'Contract',
    title: 'Read the data format',
    text: 'See how products, changes, search indexes, histories, and source records are stored.',
    to: '/docs/technical-details/data-schema',
  },
  {
    eyebrow: 'Design',
    title: 'Understand the architecture',
    text: 'See how monthly collection, validation, and GitHub Pages publication work.',
    to: '/docs/technical-details/architecture',
  },
];

const previewRows = [
  ['700579', 'Retail price', '11.26', '10.12'],
  ['Product', 'Added', 'absent', 'present'],
  ['Product', 'Removed', 'present', 'absent'],
];

export default function Home() {
  const logoUrl = useBaseUrl('/img/nomenclator-delta-logo.svg');

  return (
    <Layout
      title="Monthly Nomenclátor changes"
      description="Search monthly changes in Spain's official Nomenclátor de facturación.">
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.delta} aria-hidden="true">Δ</div>
          <div className={styles.heroGrid}>
            <div className={styles.copy}>
              <p className={styles.kicker}>Compare monthly releases</p>
              <h1>See what changed in the Nomenclátor.</h1>
              <p className={styles.lede}>
                The Nomenclátor is the Ministry's monthly database of medicines
                and health products in the SNS pharmaceutical benefit that are
                dispensed through community pharmacies. Search changes by
                Código Nacional, medicine, active ingredient, or laboratory.
              </p>
              <div className={styles.actions}>
                <Link className="button button--primary button--lg" to="pathname:///app/">
                  Open the Spanish app
                </Link>
                <Link className="button button--secondary button--lg" to="/docs/overview">
                  Read the docs
                </Link>
              </div>
            </div>

            <div className={styles.diffPanel} aria-label="Example change records">
              <div className={styles.panelHeader}>
                <img src={logoUrl} alt="" />
                <div>
                  <strong>Two consecutive months</strong>
                  <span>Matched by Código Nacional</span>
                </div>
                <i aria-hidden="true" />
              </div>
              <div className={styles.columnLabels} aria-hidden="true">
                <span>Presentation</span>
                <span>Change</span>
                <span>Before</span>
                <span>After</span>
              </div>
              <div className={styles.previewTable} aria-hidden="true">
                {previewRows.map((row) => (
                  <div className={styles.previewRow} key={row.join('-')}>
                    {row.map((cell, index) => (
                      <span className={index === 3 ? styles.after : undefined} key={`${index}-${cell}`}>
                        {cell}
                      </span>
                    ))}
                  </div>
                ))}
              </div>
              <div className={styles.statusRow}>
                <span>Official source</span>
                <span>Static JSON</span>
                <span>Source details</span>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.section} id="user-docs" aria-labelledby="user-heading">
          <header className={styles.sectionHeader}>
            <p>For pharmacy professionals</p>
            <h2 id="user-heading">Find a change and check its source.</h2>
          </header>
          <div className={styles.cardGrid}>
            {userLinks.map((item) => (
              <Link className={styles.card} to={item.to} key={item.title}>
                <span>{item.eyebrow}</span>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
                <b aria-hidden="true">→</b>
              </Link>
            ))}
          </div>
        </section>

        <section className={`${styles.section} ${styles.developerSection}`} id="developer-docs" aria-labelledby="developer-heading">
          <header className={styles.sectionHeader}>
            <p>For developers and maintainers</p>
            <h2 id="developer-heading">How the data is built and published.</h2>
          </header>
          <div className={styles.cardGrid}>
            {developerLinks.map((item) => (
              <Link className={styles.card} to={item.to} key={item.title}>
                <span>{item.eyebrow}</span>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
                <b aria-hidden="true">→</b>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </Layout>
  );
}
