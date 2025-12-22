import React, { useEffect, useState } from "react";

export default function Cursor() {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [trail, setTrail] = useState({ x: 0, y: 0 });

  useEffect(() => {
    let animationFrame: number | null = null;

    const updateTrail = () => {
      setTrail((prev) => ({
        x: prev.x + (position.x - prev.x) * 0.2,
        y: prev.y + (position.y - prev.y) * 0.2,
      }));
      animationFrame = requestAnimationFrame(updateTrail);
    };

    animationFrame = requestAnimationFrame(updateTrail);
    return () => {
      if (animationFrame) cancelAnimationFrame(animationFrame);
    };
  }, [position]);

  useEffect(() => {
    const handleMove = (event: MouseEvent) => {
      setPosition({ x: event.clientX, y: event.clientY });
    };

    window.addEventListener("mousemove", handleMove);
    return () => window.removeEventListener("mousemove", handleMove);
  }, []);

  return (
    <>
      <div
        className="custom-cursor"
        style={{
          transform: `translate3d(${position.x}px, ${position.y}px, 0)`,
        }}
        aria-hidden
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path
            d="M3 3L10.07 19.97L12.58 12.58L19.97 10.07L3 3Z"
            fill="url(#gradient)"
            stroke="white"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
          <defs>
            <linearGradient id="gradient" x1="3" y1="3" x2="19.97" y2="19.97">
              <stop offset="0%" stopColor="#fbb6ce" />
              <stop offset="50%" stopColor="#fef08a" />
              <stop offset="100%" stopColor="#4f46e5" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <div
        className="custom-cursor__trail"
        style={{ transform: `translate3d(${trail.x - 2}px, ${trail.y - 2}px, 0)` }}
        aria-hidden
      />

      <style>{`
        * { cursor: none !important; }
        .custom-cursor {
          position: fixed;
          top: 0;
          left: 0;
          pointer-events: none;
          z-index: 10001;
          transition: transform 80ms ease-out;
        }
        .custom-cursor__trail {
          position: fixed;
          top: 0;
          left: 0;
          width: 4px;
          height: 4px;
          border-radius: 999px;
          background: linear-gradient(135deg, #fbb6ce 0%, #fef08a 50%, #4f46e5 100%);
          opacity: 0.6;
          pointer-events: none;
          z-index: 10000;
          transition: transform 140ms ease-out;
        }
      `}</style>
    </>
  );
}