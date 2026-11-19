import Image from "next/image";
import Link from "next/link";

const STEPS = [
  ["01", "Create your account", "Use your email to register and securely return to your application."],
  ["02", "Tell us your story", "Share your background, location and entrepreneurship interests."],
  ["03", "Verify & track", "Upload your identity documents and follow each stage of review."],
];

export default function Overview() {
  return (
    <section>
      <div className="eyebrow">NORTHERN YOUTH EMPOWERMENT</div>
      <div className="hero">
        <div>
          <h1>
            Your ambition.
            <br />
            Our shared <em>future.</em>
          </h1>
          <p>
            Introducing the proposed 5,000 Youth Global Entrepreneurship Initiative: individual US LLC formation
            coordination, practical entrepreneurship development and digital business skills across the 19 Northern
            States.
          </p>
          <Link className="button primary" href="/apply">
            Start your application <span aria-hidden="true">↗</span>
          </Link>
          <p className="fine">Application does not guarantee selection.</p>
        </div>
        <div className="programmeArt">
          <Image
            src="/assets/empowerment-brief.jpeg"
            alt="Empowerment programme artwork featuring Senator Godswill Obot Akpabio and Renewed Hope branding"
            width={1117}
            height={1617}
            sizes="(max-width: 900px) 100vw, 40vw"
            priority
          />
          <Link href="/programme">Explore the empowerment programme →</Link>
        </div>
      </div>

      <div className="stats">
        <div>
          <strong>19</strong>
          <span>Northern states</span>
        </div>
        <div>
          <strong>5,000</strong>
          <span>Proposed youth beneficiaries</span>
        </div>
        <div>
          <strong>1</strong>
          <span>Connected application portal</span>
        </div>
      </div>

      <div className="sectionHead">
        <h2>A clear path from ambition to opportunity</h2>
        <span>THE APPLICATION JOURNEY</span>
      </div>
      <div className="cards">
        {STEPS.map(([n, title, text]) => (
          <article key={n}>
            <i>{n}</i>
            <h3>{title}</h3>
            <p>{text}</p>
          </article>
        ))}
      </div>

      <div className="info">
        <b>Prepare before you apply</b>
        <span>International Passport or NIN slip · Recent passport photograph · Business idea</span>
        <Link href="/apply">View application →</Link>
      </div>
    </section>
  );
}
