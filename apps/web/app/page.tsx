import Image, { type ImageProps } from "next/image";
import Link from "next/link";
import { auth } from "../auth";
import styles from "./page.module.css";

type Props = Omit<ImageProps, "src"> & {
  srcLight: string;
  srcDark: string;
};

const ThemeImage = (props: Props) => {
  const { srcLight, srcDark, ...rest } = props;

  return (
    <>
      <Image {...rest} src={srcLight} className="imgLight" />
      <Image {...rest} src={srcDark} className="imgDark" />
    </>
  );
};

export default async function Home() {
  const session = await auth();

  return (
    <div className={styles.page}>
      <header
        style={{
          width: "100%",
          maxWidth: "800px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "1rem 0",
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        <span style={{ fontWeight: 600, fontSize: "1rem" }}>VULMS AI Companion</span>
        <div>
          {session?.user ? (
            <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
              <span style={{ fontSize: "0.875rem", opacity: 0.8 }}>
                {session.user.name ?? session.user.email}
              </span>
              <Link
                href="/dashboard"
                style={{
                  padding: "0.4rem 0.875rem",
                  borderRadius: "6px",
                  backgroundColor: "#27272a",
                  color: "#fff",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  border: "1px solid #3f3f46",
                }}
              >
                Dashboard
              </Link>
            </div>
          ) : (
            <Link
              href="/login"
              style={{
                padding: "0.4rem 0.875rem",
                borderRadius: "6px",
                backgroundColor: "#fafafa",
                color: "#09090b",
                fontSize: "0.875rem",
                fontWeight: 600,
              }}
            >
              Sign In
            </Link>
          )}
        </div>
      </header>

      <main className={styles.main}>
        <ThemeImage
          className={styles.logo}
          srcLight="turborepo-dark.svg"
          srcDark="turborepo-light.svg"
          alt="Turborepo logo"
          width={180}
          height={38}
          priority
        />
        <ol>
          <li>
            Get started by editing <code>apps/web/app/page.tsx</code>
          </li>
          <li>Save and see your changes instantly.</li>
        </ol>

        <div className={styles.ctas}>
          {session?.user ? (
            <Link className={styles.primary} href="/dashboard">
              Go to Dashboard
            </Link>
          ) : (
            <Link className={styles.primary} href="/login">
              Sign In with Google
            </Link>
          )}
          <a
            href="https://turborepo.dev/docs?utm_source"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.secondary}
          >
            Read our docs
          </a>
        </div>
      </main>
      <footer className={styles.footer}>
        <a
          href="https://vercel.com/templates?search=turborepo&utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/window.svg"
            alt="Window icon"
            width={16}
            height={16}
          />
          Examples
        </a>
        <a
          href="https://turborepo.dev?utm_source=create-turbo"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/globe.svg"
            alt="Globe icon"
            width={16}
            height={16}
          />
          Go to turborepo.dev →
        </a>
      </footer>
    </div>
  );
}
