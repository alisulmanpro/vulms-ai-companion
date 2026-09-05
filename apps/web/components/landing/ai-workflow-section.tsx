import { AI_WORKFLOW_POINTS } from "./landing-data";
import { ScrollReveal } from "./scroll-reveal";
import styles from "./ai-workflow-section.module.css";

export function AiWorkflowSection() {
  return (
    <section className={styles.section}>
      <div className={styles.container}>
        <ScrollReveal>
          <p className={styles.eyebrow}>Intelligent Workflow</p>
          <h2 className={styles.title}>From LMS change to actionable alert</h2>
          <p className={styles.subtitle}>
            The companion pipeline observes academic data, detects meaningful changes,
            and queues notifications through the backend.
          </p>
        </ScrollReveal>

        <div className={styles.pipeline}>
          {AI_WORKFLOW_POINTS.map((point, index) => (
            <ScrollReveal key={point.title} delay={index * 100}>
              <article className={styles.node}>
                <span className={styles.nodeIndex}>{index + 1}</span>
                <h3>{point.title}</h3>
                <p>{point.description}</p>
                {index < AI_WORKFLOW_POINTS.length - 1 ? (
                  <span className={styles.connector} aria-hidden="true" />
                ) : null}
              </article>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
