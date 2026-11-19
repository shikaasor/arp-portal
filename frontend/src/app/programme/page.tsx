import type { Metadata } from "next";
import Link from "next/link";
import { Img } from "@/components/Img";

export const metadata: Metadata = { title: "Programme brief" };

const STRUCTURE = [
  ["Beneficiaries", "Up to 5,000 young entrepreneurs"],
  ["Geographic coverage", "19 Northern States"],
  ["Business structure", "Individual US LLCs"],
  ["Formation coordination", "Marich Global Technologies"],
  ["Mobilisation", "Arewa Revival Project"],
  ["Entrepreneurship network", "NACCIMA Youth Entrepreneurs, subject to agreement"],
  ["Business advisory", "Elieson Business Consulting, subject to agreement"],
  ["Professional formation", "Qualified US-based providers"],
  ["Training", "Digital business, compliance and entrepreneurship"],
  ["Monitoring", "Joint programme reporting"],
];

const ICON = {
  company: "M3 21h18M5 21V9l7-5 7 5v12M9 21v-6h6v6M9 11h.01M15 11h.01",
  training: "M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3Z",
  network: "M16 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM2 20c0-3 2.7-5 6-5s6 2 6 5M14 15.3c.6-.2 1.3-.3 2-.3 3.3 0 6 2 6 5",
};

const PILLARS = [
  { icon: ICON.company, title: "Your own US company", text: "Each selected entrepreneur gets an individual US LLC, formed by qualified US-based providers." },
  { icon: ICON.training, title: "Practical training", text: "Digital business, compliance and entrepreneurship skills to run and grow your company." },
  { icon: ICON.network, title: "Networks & advisory", text: "Access to entrepreneurship networks and business advisory partners, subject to agreement." },
];

export default function Programme() {
  return (
    <>
      <section className="pageHero imageHero">
        <Img name="zaria" sizes="100vw" className="pageHeroBg" priority />
        <div className="pageHeroInner">
          <p className="eyebrow light">The flagship programme · Proposed initiative</p>
          <h1>
            5,000 Youth Global
            <br />
            <em>Entrepreneurship</em> Initiative
          </h1>
          <p className="lead">
            Northern Youth Renewed Hope Mega March, National Development Summit and International Entrepreneurship
            Empowerment Programme.
          </p>
        </div>
      </section>
      <div className="zigzag" aria-hidden="true" />

      <section className="section">
        <div className="patron">
          <Img name="seal" sizes="96px" />
          <div>
            <p className="eyebrow">Grand Patron · Arewa Revival Project</p>
            <h2>His Excellency, Sen. Godswill Obot Akpabio, GCON</h2>
            <p className="muted">President of the Senate, Federal Republic of Nigeria</p>
          </div>
        </div>

        <div className="pillars">
          {PILLARS.map((p) => (
            <article key={p.title}>
              <span className="pillarIcon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d={p.icon} />
                </svg>
              </span>
              <h3>{p.title}</h3>
              <p>{p.text}</p>
            </article>
          ))}
        </div>

        <div className="briefLayout">
          <div>
            <h2>Connecting entrepreneurs to global opportunities</h2>
            <p>
              The proposed flagship initiative will support up to 5,000 selected young entrepreneurs from the 19
              Northern States of Nigeria. The programme will combine individual US LLC formation coordination with
              practical entrepreneurship development.
            </p>
            <p>
              Marich Global Technologies will coordinate formation, with professional formation delivered by qualified
              US-based providers. Training will cover digital business, compliance and entrepreneurship.
            </p>
            <div className="heroActions">
              <Link className="button primary large" href="/apply">
                Start your application →
              </Link>
            </div>
            <p className="fine">This is a proposed programme. Applying does not guarantee selection or company formation.</p>
          </div>
          <a className="briefImage" href="/assets/empowerment-brief.jpeg" target="_blank" rel="noopener">
            <Img name="brief" sizes="(max-width: 900px) 90vw, 30vw" />
            <span>Open the original programme brief ↗</span>
          </a>
        </div>

        <h2>Proposed programme structure</h2>
        <div className="tableWrap">
          <table className="programmeTable">
            <thead>
              <tr>
                <th scope="col">Programme component</th>
                <th scope="col">Proposed delivery</th>
              </tr>
            </thead>
            <tbody>
              {STRUCTURE.map(([k, v]) => (
                <tr key={k}>
                  <th scope="row">{k}</th>
                  <td>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="ctaBand compact">
        <Img name="katsina" sizes="100vw" className="ctaBg" />
        <div className="ctaInner">
          <h2>
            Ready to <em>build?</em>
          </h2>
          <p>Applications are reviewed state by state, then LGA and ward.</p>
          <Link className="button gold large" href="/apply">
            Apply now →
          </Link>
        </div>
      </section>
    </>
  );
}
