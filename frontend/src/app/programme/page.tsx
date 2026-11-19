import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

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

export default function Programme() {
  return (
    <section>
      <div className="eyebrow">THE FLAGSHIP PROGRAMME · PROPOSED INITIATIVE</div>
      <h1>
        5,000 Youth Global
        <br />
        Entrepreneurship Initiative
      </h1>
      <p className="programmeIntro">
        Northern Youth Renewed Hope Mega March, National Development Summit and International Entrepreneurship
        Empowerment Programme.
      </p>

      <div className="patron panel">
        <Image src="/assets/senate-president-seal.png" alt="President of the Senate, Federal Republic of Nigeria seal" width={90} height={90} />
        <div>
          <div className="eyebrow">GRAND PATRON · AREWA REVIVAL PROJECT</div>
          <h2>His Excellency, Sen. Godswill Obot Akpabio, GCON</h2>
          <p>President of the Senate, Federal Republic of Nigeria</p>
        </div>
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
          <Link className="button primary" href="/apply">
            Start your application ↗
          </Link>
          <p className="fine">This is a proposed programme. Application does not guarantee selection or company formation.</p>
        </div>
        <a className="briefImage" href="/assets/empowerment-brief.jpeg" target="_blank" rel="noopener">
          <Image src="/assets/empowerment-brief.jpeg" alt="Original empowerment programme brief" width={1117} height={1617} sizes="(max-width: 900px) 360px, 30vw" />
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
  );
}
