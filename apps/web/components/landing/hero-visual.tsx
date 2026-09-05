"use client";

import Image from "next/image";
import { usePrefersReducedMotion } from "./hooks/use-prefers-reduced-motion";
import styles from "./hero-visual.module.css";

type HeroVisualProps = {
  scrollY: number;
};

export function HeroVisual({ scrollY }: HeroVisualProps) {
  const prefersReducedMotion = usePrefersReducedMotion();

  const parallaxY = prefersReducedMotion ? 0 : Math.min(scrollY * 0.12, 80);
  const scale = prefersReducedMotion ? 1 : Math.max(1 - scrollY / 2800, 0.92);
  const opacity = prefersReducedMotion ? 1 : Math.max(1 - scrollY / 900, 0.55);

  return (
    <div
      className={styles.stage}
      style={{
        transform: `translate3d(0, ${-parallaxY}px, 0) scale(${scale})`,
        opacity,
      }}
      aria-hidden="true"
    >
      {/* <Image
        src="/hero-triangle.svg"
        alt=""
        width={800}
        height={600}
        className={styles.svg}
        priority
        draggable={false}
      /> */}
    </div>
  );
}
