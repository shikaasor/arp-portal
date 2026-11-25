"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Img } from "@/components/Img";
import { images, type ImageKey } from "@/lib/images.generated";

/** Thumbnail grid that opens each photo full-size in a keyboard-navigable lightbox. */
export function Gallery({ keys, label }: { keys: ImageKey[]; label: string }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [index, setIndex] = useState(0);

  const open = (i: number) => {
    setIndex(i);
    dialog.current?.showModal();
  };
  const step = useCallback((d: number) => setIndex((i) => (i + d + keys.length) % keys.length), [keys.length]);

  useEffect(() => {
    const el = dialog.current;
    if (!el) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") step(1);
      if (e.key === "ArrowLeft") step(-1);
    };
    el.addEventListener("keydown", onKey);
    return () => el.removeEventListener("keydown", onKey);
  }, [step]);

  const current = images[keys[index]];

  return (
    <>
      <ul className="gallery" aria-label={label}>
        {keys.map((key, i) => (
          <li key={key}>
            <button type="button" onClick={() => open(i)} aria-label={`Enlarge: ${images[key].alt}`}>
              <Img name={key} sizes="(max-width: 600px) 50vw, (max-width: 1000px) 33vw, 300px" />
            </button>
          </li>
        ))}
      </ul>

      <dialog
        ref={dialog}
        className="lightbox"
        aria-label={label}
        onClick={(e) => e.target === dialog.current && dialog.current.close()}
      >
        <figure>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={current.src} width={current.width} height={current.height} alt={current.alt} />
          <figcaption>
            <span>{current.alt}</span>
            <span className="lightboxCount">
              {index + 1} / {keys.length}
            </span>
          </figcaption>
        </figure>
        <button type="button" className="lightboxNav prev" onClick={() => step(-1)} aria-label="Previous photo">
          ‹
        </button>
        <button type="button" className="lightboxNav next" onClick={() => step(1)} aria-label="Next photo">
          ›
        </button>
        <button type="button" className="lightboxClose" onClick={() => dialog.current?.close()} aria-label="Close">
          ×
        </button>
      </dialog>
    </>
  );
}
