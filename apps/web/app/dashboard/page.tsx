import { auth, signOut } from "../../auth";
import { redirect } from "next/navigation";
import Image from "next/image";
import styles from "./dashboard.module.css";

export const metadata = {
  title: "Dashboard - VULMS AI Companion",
  description: "User dashboard and authentication verification",
};

export default async function DashboardPage() {
  const session = await auth();

  if (!session?.user) {
    redirect("/login");
  }

  const user = session.user;

  return (
    <main className={styles.container}>
      <div className={styles.card}>
        {user.image ? (
          <Image
            src={user.image}
            alt={user.name ?? "User avatar"}
            width={72}
            height={72}
            className={styles.avatar}
            unoptimized
          />
        ) : (
          <div className={styles.avatarPlaceholder} aria-hidden="true">
            {user.name ? user.name.charAt(0).toUpperCase() : "U"}
          </div>
        )}

        <h1 className={styles.title}>Welcome, {user.name ?? "Student"}!</h1>
        <p className={styles.email}>{user.email}</p>

        <div className={styles.infoGrid}>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>User ID</span>
            <span className={styles.infoValue}>{user.id ?? "N/A"}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Provider</span>
            <span className={styles.infoValue}>Google OAuth</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Status</span>
            <span className={styles.infoValue} style={{ color: "#4ade80" }}>
              Authenticated
            </span>
          </div>
        </div>

        <form
          action={async () => {
            "use server";
            await signOut({ redirectTo: "/login" });
          }}
          style={{ width: "100%" }}
        >
          <button type="submit" className={styles.signOutBtn}>
            Sign Out
          </button>
        </form>
      </div>
    </main>
  );
}
