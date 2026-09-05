import { ScrollReveal } from "./scroll-reveal";
import styles from "./value-proposition-section.module.css";

export function ValuePropositionSection() {
  return (
    <section id="about" className={styles.section}>
      <div className={styles.container}>
        <ScrollReveal>
          <p className={styles.eyebrow}>Why VULMS AI Companion</p>
          <h2 className={styles.title}>
            Your academic workflow, monitored intelligently
          </h2>
          <p className={styles.lead}>
            VULMS AI Companion connects your browser extension, web dashboard, and
            backend watcher into one system — so deadlines, quizzes, and fee alerts
            reach you before they become problems.
          </p>
        </ScrollReveal>

        <div className={styles.grid}>
          <ScrollReveal delay={80}>
            <article className={styles.card}>
              <h3>For VU students</h3>
              <p>
                Built around vulms.vu.edu.pk — assignments, quizzes, GDBs, and
                challan summaries in one companion.
              </p>
            </article>
          </ScrollReveal>
          <ScrollReveal delay={160}>
            <article className={styles.card}>
              <h3>Secure by design</h3>
              <p>
                Google OAuth through Auth.js, server-side sessions, and encrypted
                credential storage on the backend.
              </p>
            </article>
          </ScrollReveal>
          <ScrollReveal delay={240}>
            <article className={styles.card}>
              <h3>Always watching</h3>
              <p>
                Extension observer plus scheduled server cycles keep your LMS data
                in sync without manual checking.
              </p>
            </article>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
