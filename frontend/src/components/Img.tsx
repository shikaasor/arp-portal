import { images, type ImageKey } from "@/lib/images.generated";

type Props = {
  name: ImageKey;
  /** CSS `sizes` hint so the browser picks the right file. */
  sizes: string;
  className?: string;
  priority?: boolean;
  alt?: string;
};

/**
 * Responsive image from the pre-optimised set in public/img (see scripts/build-images.py).
 * We don't use next/image: its /_next/image optimiser isn't available under Vercel Services.
 */
export function Img({ name, sizes, className, priority, alt }: Props) {
  const img = images[name];
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={img.src}
      srcSet={img.srcSet}
      sizes={sizes}
      width={img.width}
      height={img.height}
      alt={alt ?? img.alt}
      className={className}
      loading={priority ? "eager" : "lazy"}
      fetchPriority={priority ? "high" : undefined}
      decoding="async"
    />
  );
}
