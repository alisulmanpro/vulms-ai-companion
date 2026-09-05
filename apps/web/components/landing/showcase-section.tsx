import { ScrollReveal } from "./scroll-reveal";
import styles from "./showcase-section.module.css";

export function ShowcaseSection() {
  return (
    <section className={styles.section}>
      <div className={styles.container}>
        <ScrollReveal>
          <div className={styles.showcase}>
            <div className={styles.glowBorder} aria-hidden="true" />
            <div className={styles.inner}>
              <div className={styles.topBar}>
                <span className={styles.dot} />
                <span className={styles.dot} />
                <span className={styles.dot} />
                <span className={styles.title}>VULMS AI Companion Dashboard</span>
              </div>
              <div className={styles.body}>
                <div className={styles.panel}>
                  <div className={styles.panelLineWide} />
                  <div className={styles.panelLine} />
                  <div className={styles.panelLine} />
                  <div className={styles.panelLineShort} />
                </div>
                <div className={styles.panelHighlight}>
                  <p className={styles.highlightLabel}>Next deadline</p>
                  <p className={styles.highlightValue}>Assignment · CS101</p>
                  <p className={styles.highlightMeta}>Alert queued via WhatsApp</p>
                </div>
                <div className={styles.panel}>
                  <div className={styles.panelLine} />
                  <div className={styles.panelLineShort} />
                </div>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
