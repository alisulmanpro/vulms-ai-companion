import { CAPABILITIES } from "./landing-data";
import { ScrollReveal } from "./scroll-reveal";
import styles from "./capabilities-section.module.css";

export function CapabilitiesSection() {
  return (
    <section className={styles.section}>
      <div className={styles.container}>
        {CAPABILITIES.map((item, index) => (
          <ScrollReveal key={item.label} delay={index * 60}>
            <article className={styles.item}>
              <p className={styles.label}>{item.label}</p>
              <p className={styles.detail}>{item.detail}</p>
            </article>
          </ScrollReveal>
        ))}
      </div>
    </section>
  );
}
