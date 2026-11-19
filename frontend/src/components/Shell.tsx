"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthDialog } from "./AuthDialog";
import { useAuth } from "./AuthProvider";

const NAV = [
  { href: "/", label: "Overview", icon: "◈" },
  { href: "/programme", label: "Programme brief", icon: "✦" },
  { href: "/apply", label: "My application", icon: "＋" },
  { href: "/status", label: "Application status", icon: "◎" },
  { href: "/admin", label: "Administration", icon: "▦" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { configured, session, openAuth, signOut } = useAuth();

  return (
    <>
      <aside className="sidebar">
        <Link className="brand" href="/">
          <Image className="brandLogo" src="/assets/arp-logo.jpeg" alt="Arewa Revival Project logo" width={68} height={56} priority />
          <span>
            AREWA REVIVAL
            <br />
            <small>PROJECT · EMPOWERMENT</small>
          </span>
        </Link>
        <div className="navLabel">YOUR OPPORTUNITY STARTS HERE</div>
        <nav aria-label="Main">
          {NAV.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link key={item.href} href={item.href} className={active ? "active" : undefined} aria-current={active ? "page" : undefined}>
                <span aria-hidden="true">{item.icon}</span> {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="asideBottom">
          19 states. One shared future.
          <p>Connecting Northern youth to opportunities for growth.</p>
          <small>AREWA REVIVAL PROJECT © {new Date().getFullYear()}</small>
        </div>
      </aside>
      <div className="shell">
        <header className="topbar">
          <span>
            Empowerment programme <span className="year">2026</span>
          </span>
          {session ? (
            <button onClick={() => void signOut()} title="Sign out">
              Sign out · <span className="email">{session.user.email}</span>
            </button>
          ) : (
            <button onClick={openAuth}>Sign in / Create account ↗</button>
          )}
        </header>
        <main id="main">
          {!configured && (
            <div className="notice" role="status">
              Preview mode · Applications open once the portal is connected to its secure backend.
            </div>
          )}
          {children}
        </main>
        <footer className="footer">
          Arewa Revival Project <span>Empowering ambition. Building opportunity.</span>
        </footer>
      </div>
      <AuthDialog />
    </>
  );
}
