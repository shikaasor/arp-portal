import type { Metadata } from "next";
import { Gallery } from "@/components/Gallery";
import { Img } from "@/components/Img";
import { PageBanner } from "@/components/PageBanner";
import { images, type ImageKey, type SiteImage } from "@/lib/images.generated";

export const metadata: Metadata = { title: "Gallery & photo credits" };

const keys = Object.keys(images) as ImageKey[];
const credited = keys.filter((k) => (images[k] as SiteImage).credit);
const senate = keys.filter((k) => (images[k] as SiteImage).gallery === "senate");

export default function Credits() {
  return (
    <>
      <PageBanner eyebrow="Gallery & thanks" title={<>Photos &amp; <em>credits</em></>}>
        Moments from the Arewa Revival Project, and the photographers whose work appears across this site. Creative
        Commons images are resized and cropped for the web; adapted versions are shared under the same licence as the
        original.
      </PageBanner>
      <section className="section galleryIntro">
        <div className="sectionHead">
          <p className="eyebrow">Arewa Revival Project · Photo gallery</p>
          <h2>
            A visit to the <span className="hl">President of the Senate</span>
          </h2>
          <p className="muted">
            The Arewa Revival Project presented the Par-Excellence Award to His Excellency, Sen. Godswill Obot Akpabio,
            GCON, President of the Senate and Grand Patron of the project, ahead of the Northern Youth Renewed Hope
            Mega March &amp; Summit. Select a photo to enlarge it.
          </p>
        </div>
        <Gallery keys={senate} label="Par-Excellence Award presentation to the President of the Senate" />
        <p className="fine">Photographs and programme artwork © Arewa Revival Project.</p>
      </section>

      <section className="section creditsList">
        <div className="sectionHead">
          <p className="eyebrow">Creative Commons</p>
          <h2>Northern Nigeria photography</h2>
        </div>
        <ul className="creditGrid">
          {credited.map((key) => {
            const c = (images[key] as SiteImage).credit;
            if (!c) return null;
            return (
              <li key={key}>
                <Img name={key} sizes="(max-width: 600px) 100vw, 320px" />
                <div>
                  <a href={c.sourceUrl} target="_blank" rel="noopener noreferrer">
                    {c.title}
                  </a>
                  <p>
                    by{" "}
                    {c.creatorUrl ? (
                      <a href={c.creatorUrl} target="_blank" rel="noopener noreferrer">
                        {c.creator}
                      </a>
                    ) : (
                      c.creator
                    )}
                  </p>
                  <p>
                    <a href={c.licenseUrl} target="_blank" rel="noopener noreferrer license">
                      {c.license}
                    </a>
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
        <p className="muted">
          Decorative patterns are original artwork for the Arewa Revival Project. Programme artwork and the ARP logo are
          © Arewa Revival Project.
        </p>
      </section>
    </>
  );
}
