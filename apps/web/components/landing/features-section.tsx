import { FEATURES } from "./landing-data";
import { ScrollReveal } from "./scroll-reveal";
import styles from "./features-section.module.css";

export function FeaturesSection() {
  return (
    <section id="features" className={styles.section}>
      <div className={styles.container}>
        <ScrollReveal>
          <p className={styles.eyebrow}>Features</p>
          <h2 className={styles.title}>Everything your LMS workflow needs</h2>
          <p className={styles.subtitle}>
            Honest capabilities from the actual product — extension, server, and web working together.
          </p>
        </ScrollReveal>

        <div className={styles.grid}>
          {FEATURES.map((feature, index) => (
            <ScrollReveal key={feature.title} delay={index * 70}>
              <article className={`${styles.card} ${styles[feature.accent]}`}>
                <div className={styles.cardGlow} aria-hidden="true" />
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </article>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
