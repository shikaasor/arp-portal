"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuthDialog } from "./AuthDialog";
import { useAuth } from "./AuthProvider";
import { Img } from "./Img";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/programme", label: "Programme" },
  { href: "/apply", label: "Apply" },
  { href: "/status", label: "My status" },
  { href: "/admin", label: "Reviewers" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { configured, session, openAuth, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const close = () => setMenuOpen(false);

  return (
    <>
      <div className="flagStripe" aria-hidden="true" />
      <header className="siteHeader">
        <div className="headerInner">
          <Link className="brand" href="/" onClick={close}>
            <span className="brandBadge">
              <Img name="logo" sizes="48px" priority />
            </span>
            <span className="brandText">
              Arewa Revival
              <small>Project · Empowerment</small>
            </span>
          </Link>

          <button
            className="menuToggle"
            aria-expanded={menuOpen}
            aria-controls="site-nav"
            onClick={() => setMenuOpen((o) => !o)}
          >
            <span aria-hidden="true">{menuOpen ? "✕" : "☰"}</span>
            <span className="srOnly">Menu</span>
          </button>

          <nav id="site-nav" aria-label="Main" className={menuOpen ? "open" : undefined}>
            {NAV.map((item) => {
              const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={active ? "active" : undefined}
                  aria-current={active ? "page" : undefined}
                  onClick={close}
                >
                  {item.label}
                </Link>
              );
            })}
            <span className="navActions">
              {session ? (
                <button className="ghost" onClick={() => void signOut()} title={session.user.email ?? ""}>
                  Sign out
                </button>
              ) : (
                <button className="ghost" onClick={() => { close(); openAuth(); }}>
                  Sign in
                </button>
              )}
              <Link className="button gold" href="/apply" onClick={close}>
                Apply now
              </Link>
            </span>
          </nav>
        </div>
      </header>

      {!configured && (
        <div className="previewBanner" role="status">
          Preview mode · Applications open once the portal is connected to its secure backend.
        </div>
      )}

      <main id="main">{children}</main>

      <footer className="siteFooter">
        <div className="zigzag" aria-hidden="true" />
        <div className="footerInner">
          <div>
            <Link className="brand light" href="/">
              <span className="brandBadge">
                <Img name="logo" sizes="48px" />
              </span>
              <span className="brandText">
                Arewa Revival
                <small>Project · Empowerment</small>
              </span>
            </Link>
            <p className="footerTag">19 states. One shared future.</p>
            <p>Connecting Northern youth to opportunities for growth.</p>
          </div>
          <div>
            <h3>Portal</h3>
            <ul>
              <li><Link href="/programme">Programme brief</Link></li>
              <li><Link href="/apply">Start an application</Link></li>
              <li><Link href="/status">Track my application</Link></li>
              <li><Link href="/admin">Reviewer workspace</Link></li>
            </ul>
          </div>
          <div>
            <h3>About</h3>
            <ul>
              <li><Link href="/credits">Gallery &amp; photo credits</Link></li>
              <li><a href="/api/docs">API documentation</a></li>
            </ul>
            <p className="fine">
              This is a proposed programme. Applying does not guarantee selection or company formation.
            </p>
          </div>
        </div>
        <div className="footerBase">
          <span>© {new Date().getFullYear()} Arewa Revival Project</span>
          <span>Empowering ambition. Building opportunity.</span>
        </div>
      </footer>
      <AuthDialog />
    </>
  );
}
