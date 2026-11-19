import Link from "next/link";

export default function NotFound() {
  return (
    <section>
      <div className="eyebrow">PAGE NOT FOUND</div>
      <h1>We couldn’t find that page.</h1>
      <Link className="button primary" href="/">
        Back to overview
      </Link>
    </section>
  );
}
