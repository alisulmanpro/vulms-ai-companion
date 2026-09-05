import { auth } from "../auth";
import { LandingPage } from "../components/landing/landing-page";

export default async function Home() {
  const session = await auth();

  return (
    <LandingPage
      isAuthenticated={!!session?.user}
      userName={session?.user?.name ?? session?.user?.email}
    />
  );
}
