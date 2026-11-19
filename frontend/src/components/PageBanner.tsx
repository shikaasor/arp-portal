/** Compact patterned banner used at the top of the app pages (apply, status, admin…). */
export function PageBanner({ eyebrow, title, children }: { eyebrow: string; title: React.ReactNode; children?: React.ReactNode }) {
  return (
    <>
      <section className="pageHero pattern-knot">
        <div className="pageHeroInner">
          <p className="eyebrow light">{eyebrow}</p>
          <h1>{title}</h1>
          {children && <div className="lead">{children}</div>}
        </div>
      </section>
      <div className="zigzag" aria-hidden="true" />
    </>
  );
}
