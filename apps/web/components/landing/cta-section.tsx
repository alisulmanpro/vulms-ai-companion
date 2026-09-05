import Link from "next/link";
import { ScrollReveal } from "./scroll-reveal";
import styles from "./cta-section.module.css";

type CtaSectionProps = {
  isAuthenticated: boolean;
};

export function CtaSection({ isAuthenticated }: CtaSectionProps) {
  return (
    <section id="cta" className={styles.section}>
      <div className={styles.container}>
        <ScrollReveal direction="up">
          <div className={styles.card}>
            <p className={styles.eyebrow}>Ready to stay ahead?</p>
            <h2 className={styles.title}>Start using VULMS AI Companion</h2>
            <p className={styles.subtitle}>
              Sign in with Google, link your VULMS account, and let the companion
              handle deadline monitoring for you.
            </p>
            <Link href={isAuthenticated ? "/dashboard" : "/login"} className={styles.ctaBtn}>
              {isAuthenticated ? "Open Dashboard" : "Get Started"}
            </Link>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
