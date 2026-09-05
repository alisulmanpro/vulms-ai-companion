import Link from "next/link";
import { LANDING_NAV_LINKS } from "./landing-data";
import styles from "./landing-footer.module.css";

export function LandingFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.brandBlock}>
          <p className={styles.brand}>VULMS AI Companion</p>
          <p className={styles.tagline}>Smart LMS alerts for VU students.</p>
        </div>

        <nav className={styles.links} aria-label="Footer">
          <Link href="/">Home</Link>
          {LANDING_NAV_LINKS.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
          <Link href="/login">Sign In</Link>
        </nav>
      </div>

      <div className={styles.bottom}>
        <p className={styles.copy}>© {year} VULMS AI Companion</p>
      </div>
    </footer>
  );
}
