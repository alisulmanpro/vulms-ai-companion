"use client";

import { useEffect, useRef, useState } from "react";
import { STEPS } from "./landing-data";
import styles from "./how-it-works-section.module.css";

export function HowItWorksSection() {
  const [activeStep, setActiveStep] = useState(0);
  const stepRefs = useRef<(HTMLLIElement | null)[]>([]);

  useEffect(() => {
    const observers: IntersectionObserver[] = [];

    stepRefs.current.forEach((node, index) => {
      if (!node) return;

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry?.isIntersecting) setActiveStep(index);
        },
        { threshold: 0.55, rootMargin: "-20% 0px -20% 0px" },
      );

      observer.observe(node);
      observers.push(observer);
    });

    return () => observers.forEach((o) => o.disconnect());
  }, []);

  return (
    <section id="how-it-works" className={styles.section}>
      <div className={styles.container}>
        <p className={styles.eyebrow}>How It Works</p>
        <h2 className={styles.title}>Four steps to smarter LMS tracking</h2>

        <ol className={styles.steps}>
          {STEPS.map((step, index) => (
            <li
              key={step.step}
              ref={(el) => {
                stepRefs.current[index] = el;
              }}
              className={`${styles.step} ${activeStep === index ? styles.active : ""}`}
            >
              <span className={styles.stepNum}>{step.step}</span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
