import type { Metadata } from "next";
import { Img } from "@/components/Img";
import { PageBanner } from "@/components/PageBanner";
import { images, type ImageKey, type SiteImage } from "@/lib/images.generated";

export const metadata: Metadata = { title: "Photo credits" };

const credited = (Object.keys(images) as ImageKey[]).filter((k) => (images[k] as SiteImage).credit);

export default function Credits() {
  return (
    <>
      <PageBanner eyebrow="With thanks" title={<>Photo <em>credits</em></>}>
        The photographs on this site are shared by their creators under Creative Commons licences. Images are resized
        and cropped for the web; adapted versions are shared under the same licence as the original.
      </PageBanner>
      <section className="section">
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
