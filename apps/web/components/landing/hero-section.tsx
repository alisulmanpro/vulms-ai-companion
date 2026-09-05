"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { HeroVisual } from "./hero-visual";
import { usePrefersReducedMotion } from "./hooks/use-prefers-reduced-motion";
import styles from "./hero-section.module.css";

type HeroSectionProps = {
  isAuthenticated: boolean;
};

export function HeroSection({ isAuthenticated }: HeroSectionProps) {
  const [scrollY, setScrollY] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const prefersReducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    setRevealed(true);

    let rafId = 0;
    const onScroll = () => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => setScrollY(window.scrollY));
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  const contentShift = prefersReducedMotion ? 0 : Math.min(scrollY * 0.08, 48);
  const contentOpacity = prefersReducedMotion ? 1 : Math.max(1 - scrollY / 640, 0);

  return (
    <section className={styles.hero} aria-label="Hero">
      <div className={styles.heroGlow} aria-hidden="true" />

      <div
        className={`${styles.content} ${revealed ? styles.revealed : ""}`}
        style={{
          opacity: contentOpacity,
          transform: `translate3d(0, ${contentShift}px, 0)`,
        }}
      >
        <p className={styles.eyebrow}>VULMS AI Companion</p>
        <h1 className={styles.title}>Stay Ahead with AI</h1>
        <p className={styles.subtitle}>
          Track deadlines, sync your LMS, and get alerts with zero friction.
        </p>

        <div className={styles.ctaRow}>
          <Link href={isAuthenticated ? "/dashboard" : "/login"} className={styles.primaryCta}>
            {isAuthenticated ? "Open Dashboard" : "Get Started"}
          </Link>
          <a href="#features" className={styles.secondaryCta}>
            Explore Features
          </a>
        </div>
      </div>

      <div className={`${styles.visualWrap} ${revealed ? styles.revealed : ""}`}>
        <HeroVisual scrollY={scrollY} />
      </div>

      <a href="#features" className={styles.scrollHint} aria-label="Scroll to features">
        <span className={styles.scrollLine} />
        Scroll
      </a>
    </section>
  );
}
