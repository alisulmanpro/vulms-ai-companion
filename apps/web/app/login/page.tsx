import { Suspense } from "react";
import { LoginForm } from "../../components/auth/login-form";
import styles from "./login.module.css";

export const metadata = {
  title: "Sign In - VULMS AI Companion",
  description: "Sign in to your VULMS AI Companion account",
};

export default function LoginPage() {
  return (
    <main className={styles.container}>
      <Suspense fallback={<div className={styles.card} style={{ minHeight: "400px" }} />}>
        <LoginForm />
      </Suspense>
    </main>
  );
}
