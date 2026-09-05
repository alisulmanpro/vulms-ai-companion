import { ECOSYSTEM_POINTS } from "./landing-data";
import { ScrollReveal } from "./scroll-reveal";
import styles from "./extension-showcase-section.module.css";

export function ExtensionShowcaseSection() {
  return (
    <section id="ecosystem" className={styles.section}>
      <div className={styles.container}>
        <div className={styles.copy}>
          <ScrollReveal direction="left">
            <p className={styles.eyebrow}>Ecosystem</p>
            <h2 className={styles.title}>Extension + web, working together</h2>
            <p className={styles.lead}>
              The browser extension observes LMS pages on vu.edu.pk while the web
              dashboard and backend handle authentication, storage, and notifications.
            </p>
            <ul className={styles.list}>
              {ECOSYSTEM_POINTS.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </ScrollReveal>
        </div>

        <ScrollReveal direction="right" delay={120}>
          <div className={styles.mockup} aria-hidden="true">
            <div className={styles.browserChrome}>
              <span />
              <span />
              <span />
              <div className={styles.urlBar}>vulms.vu.edu.pk</div>
            </div>
            <div className={styles.browserBody}>
              <div className={styles.sidebar}>
                <div className={styles.sidebarItem} />
                <div className={styles.sidebarItem} />
                <div className={styles.sidebarItemActive} />
              </div>
              <div className={styles.contentPane}>
                <div className={styles.contentHeader} />
                <div className={styles.contentRow} />
                <div className={styles.contentRow} />
                <div className={styles.contentRowShort} />
                <div className={styles.badge}>Extension Active</div>
              </div>
            </div>
            <div className={styles.connector}>
              <span className={styles.connectorDot} />
              <span className={styles.connectorLine} />
              <span className={styles.connectorLabel}>Sync</span>
            </div>
            <div className={styles.serverBlock}>
              <span>Web + Server</span>
              <small>Auth · Watcher · WhatsApp</small>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
