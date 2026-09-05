"use client";

import { AiWorkflowSection } from "./ai-workflow-section";
import { CapabilitiesSection } from "./capabilities-section";
import { CtaSection } from "./cta-section";
import { ExtensionShowcaseSection } from "./extension-showcase-section";
import { FeaturesSection } from "./features-section";
import { HeroSection } from "./hero-section";
import { HowItWorksSection } from "./how-it-works-section";
import { LandingFooter } from "./landing-footer";
import { LandingNavbar } from "./landing-navbar";
import { ShowcaseSection } from "./showcase-section";
import { ValuePropositionSection } from "./value-proposition-section";
import { useScrollProgress } from "./hooks/use-scroll-progress";
import styles from "./landing-page.module.css";

type LandingPageProps = {
  isAuthenticated: boolean;
  userName?: string | null;
};

export function LandingPage({ isAuthenticated, userName }: LandingPageProps) {
  const scrollProgress = useScrollProgress();

  return (
    <div className={styles.page}>
      <div
        className={styles.progressBar}
        style={{ transform: `scaleX(${scrollProgress})` }}
        aria-hidden="true"
      />

      <div className={styles.noise} aria-hidden="true" />
      <div className={styles.ambientGlow} aria-hidden="true" />

      <LandingNavbar isAuthenticated={isAuthenticated} userName={userName} />

      <main>
        <HeroSection isAuthenticated={isAuthenticated} />
        <ValuePropositionSection />
        <FeaturesSection />
        <HowItWorksSection />
        <ExtensionShowcaseSection />
        <AiWorkflowSection />
        <CapabilitiesSection />
        <ShowcaseSection />
        <CtaSection isAuthenticated={isAuthenticated} />
      </main>

      <LandingFooter />
    </div>
  );
}
