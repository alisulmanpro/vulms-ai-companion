"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { signOutAction } from "../../lib/auth-actions";
import { LANDING_NAV_LINKS } from "./landing-data";
import styles from "./landing-navbar.module.css";

type LandingNavbarProps = {
  isAuthenticated: boolean;
  userName?: string | null;
};

export function LandingNavbar({ isAuthenticated, userName }: LandingNavbarProps) {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  return (
    <header className={`${styles.navbar} ${scrolled ? styles.scrolled : ""}`}>
      <div className={styles.inner}>
        <Link href="/" className={styles.brand} onClick={() => setMenuOpen(false)}>
          <span className={styles.brandMark} aria-hidden="true" />
          VULMS AI Companion
        </Link>

        <nav className={`${styles.nav} ${menuOpen ? styles.navOpen : ""}`} aria-label="Main">
          <Link href="/" className={styles.navLink} onClick={() => setMenuOpen(false)}>
            Home
          </Link>
          {LANDING_NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className={styles.navLink}
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className={styles.actions}>
          {isAuthenticated ? (
            <>
              {userName ? <span className={styles.userName}>{userName}</span> : null}
              <Link href="/dashboard" className={styles.ghostBtn}>
                Dashboard
              </Link>
              <form action={signOutAction}>
                <button type="submit" className={styles.primaryBtn}>
                  Sign Out
                </button>
              </form>
            </>
          ) : (
            <>
              <Link href="/login" className={styles.ghostBtn}>
                Sign In
              </Link>
              <Link href="/login" className={styles.primaryBtn}>
                Get Started
              </Link>
            </>
          )}

          <button
            type="button"
            className={styles.menuBtn}
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </div>
    </header>
  );
}
