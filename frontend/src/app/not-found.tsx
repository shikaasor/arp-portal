import Link from "next/link";
import { PageBanner } from "@/components/PageBanner";

export default function NotFound() {
  return (
    <>
    <PageBanner eyebrow="Page not found" title="We couldn’t find that page." />
    <section className="section narrowSection">
      <Link className="button primary" href="/">
        Back to overview
      </Link>
    </section>
    </>
  );
}
