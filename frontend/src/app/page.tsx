import Link from "next/link";
import { Img } from "@/components/Img";
import type { ImageKey } from "@/lib/images.generated";
import { STATES } from "@/lib/options";

const STATS = [
  { value: "19", label: "Northern states + FCT" },
  { value: "5,000", label: "Young entrepreneurs" },
  { value: "US LLC", label: "Individual company formation" },
  { value: "1", label: "Portal for every applicant" },
];

const SECTORS: { title: string; text: string; image?: ImageKey; tone?: string }[] = [
  { title: "Agriculture & agribusiness", text: "From rice paddies to onion farms: grow, process and export.", image: "rice" },
  { title: "Trade & commerce", text: "Build on centuries of Northern market trading with global reach.", image: "market" },
  { title: "Fashion & textiles", text: "Weaving, tailoring and design rooted in Arewa craft.", image: "weaver" },
  { title: "Renewable energy", text: "Power homes and businesses with solar across the North.", image: "solar" },
  { title: "Creative arts & crafts", text: "Indigo dyeing, leatherwork and the creative economy.", image: "adire" },
  { title: "Technology & digital", text: "Digital services, e-commerce and the skills to sell worldwide.", tone: "indigo" },
];

const STEPS = [
  { n: "01", title: "Create your account", text: "Register with your email and verify it. You can return to your application any time." },
  { n: "02", title: "Tell us your story", text: "Share your background, your location and the business you want to build." },
  { n: "03", title: "Verify & track", text: "Upload your ID and photograph securely, then follow each stage of review." },
];

export default function Home() {
  return (
    <>
      {/* ---------- Hero ---------- */}
      <section className="hero">
        <div className="heroText pattern-knot">
          <p className="kicker">
            <span className="dot" /> Barka da zuwa · Welcome
          </p>
          <h1>
            Your ambition.
            <br />
            Our shared <em>future.</em>
          </h1>
          <p className="lead">
            The proposed <strong>5,000 Youth Global Entrepreneurship Initiative</strong>: individual US LLC formation,
            practical entrepreneurship training and digital business skills for young people across the 19 Northern
            States.
          </p>
          <div className="heroActions">
            <Link className="button gold large" href="/apply">
              Start your application <span aria-hidden="true">→</span>
            </Link>
            <Link className="button outlineLight large" href="/programme">
              Read the programme brief
            </Link>
          </div>
          <p className="fineLight">Applying does not guarantee selection.</p>
        </div>
        <div className="heroMedia">
          <Img name="hero" sizes="(max-width: 900px) 100vw, 55vw" priority />
          <span className="heroBadge">
            <strong>2026</strong> Empowerment programme
          </span>
        </div>
      </section>

      {/* ---------- States ticker ---------- */}
      <div className="ticker" aria-label="Participating states">
        <div className="tickerTrack">
          {[0, 1].map((copy) => (
            <ul key={copy} aria-hidden={copy === 1}>
              {STATES.map((s) => (
                <li key={s}>
                  <span className="knotDot" aria-hidden="true">✦</span> {s}
                </li>
              ))}
            </ul>
          ))}
        </div>
      </div>

      {/* ---------- Stats ---------- */}
      <section className="section stats">
        {STATS.map((s) => (
          <div key={s.label} className="stat">
            <strong>{s.value}</strong>
            <span>{s.label}</span>
          </div>
        ))}
      </section>

      {/* ---------- Heritage ---------- */}
      <section className="section heritage">
        <div className="heritageText">
          <p className="eyebrow">Enterprise runs deep in Arewa</p>
          <h2>
            Built on centuries of <span className="hl">Northern enterprise.</span>
          </h2>
          <p>
            From the indigo dye pits of Kano to the great markets and palace craftsmen of Zaria and Katsina, the North
            has always traded with the world. This programme connects that spirit to modern tools: a registered US
            company, digital skills and a network of partners.
          </p>
          <Link className="textLink" href="/programme">
            How the programme works →
          </Link>
        </div>
        <div className="mosaic">
          <figure className="m1">
            <Img name="dyepit" sizes="(max-width: 900px) 60vw, 26vw" />
            <figcaption>Traditional indigo dyeing</figcaption>
          </figure>
          <figure className="m2">
            <Img name="zaria" sizes="(max-width: 900px) 40vw, 18vw" />
            <figcaption>Emir&apos;s palace gate, Zaria</figcaption>
          </figure>
          <figure className="m3">
            <Img name="market" sizes="(max-width: 900px) 40vw, 18vw" />
            <figcaption>Kurmi Market, Kano</figcaption>
          </figure>
          <figure className="m4">
            <Img name="katsina" sizes="(max-width: 900px) 60vw, 26vw" />
            <figcaption>Emir&apos;s palace, Katsina</figcaption>
          </figure>
        </div>
      </section>

      {/* ---------- Sectors ---------- */}
      <section className="section sectors">
        <div className="sectionHead">
          <p className="eyebrow">Choose your path</p>
          <h2>Sectors we&apos;re looking for</h2>
          <p className="muted">Tell us which sector your business idea belongs to when you apply.</p>
        </div>
        <div className="sectorGrid">
          {SECTORS.map((s) => (
            <article key={s.title} className={`sectorCard ${s.tone ?? ""}`}>
              {s.image ? (
                <Img name={s.image} sizes="(max-width: 600px) 100vw, (max-width: 1000px) 50vw, 33vw" />
              ) : (
                <div className="sectorArt pattern-knot" aria-hidden="true">
                  <span>{"</>"}</span>
                </div>
              )}
              <div className="sectorBody">
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* ---------- Journey ---------- */}
      <section className="journey pattern-knot">
        <div className="journeyInner">
          <p className="eyebrow light">The application journey</p>
          <h2>A clear path from ambition to opportunity</h2>
          <ol className="steps">
            {STEPS.map((s) => (
              <li key={s.n}>
                <span className="stepNum">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
          <div className="prepare">
            <strong>Prepare before you apply</strong>
            <span>NIN slip or International Passport</span>
            <span>Recent passport photograph</span>
            <span>Your business idea (at least 30 words)</span>
          </div>
        </div>
      </section>

      {/* ---------- Programme teaser ---------- */}
      <section className="section teaser">
        <div className="teaserMedia">
          <Img name="durbar" sizes="(max-width: 900px) 100vw, 50vw" />
        </div>
        <div className="teaserText">
          <p className="eyebrow">The flagship programme</p>
          <h2>Connecting Northern entrepreneurs to global opportunities</h2>
          <ul className="checks">
            <li>Individual US LLC formation, coordinated by Marich Global Technologies</li>
            <li>Training in digital business, compliance and entrepreneurship</li>
            <li>Mobilisation across all 19 Northern States by the Arewa Revival Project</li>
            <li>Partner networks for advisory and mentoring, subject to agreement</li>
          </ul>
          <Link className="button primary large" href="/programme">
            Explore the programme →
          </Link>
        </div>
      </section>

      {/* ---------- CTA ---------- */}
      <section className="ctaBand">
        <Img name="jos" sizes="100vw" className="ctaBg" />
        <div className="ctaInner">
          <h2>
            Your business. <em>Global reach.</em>
          </h2>
          <p>Applications are reviewed state by state. Start yours today and keep your reference to track progress.</p>
          <Link className="button gold large" href="/apply">
            Apply now →
          </Link>
        </div>
      </section>
    </>
  );
}
