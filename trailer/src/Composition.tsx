import React, { useEffect } from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  delayRender,
  continueRender,
  Easing,
} from "remotion";

const FPS = 30;
const DURATION_S = 45;

// ─── Color palette (matches the landing page) ─────────────────────
const INK = "#0F0E0D";
const BONE = "#F5F1E8";
const PRIMARY = "#C4A484";
const PRIMARY_DEEP = "#A68B6F";

// ─── Font loader ──────────────────────────────────────────────────
const FONT_URL =
  "https://fonts.googleapis.com/css2?family=Anton&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,700;1,9..144,300;1,9..144,700&display=swap";

const useFonts = () => {
  const [handle] = React.useState(() => delayRender("Loading fonts"));
  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = FONT_URL;
    link.onload = () => {
      (document as any).fonts.ready.then(() => continueRender(handle));
    };
    link.onerror = () => continueRender(handle);
    document.head.appendChild(link);
  }, [handle]);
};

// ─── Drift fog (animated blobs over background) ───────────────────
const DriftFog: React.FC<{ intensity?: number }> = ({ intensity = 1 }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;

  const blob = (
    cx: number,
    cy: number,
    r: number,
    color: string,
    speed: number,
    phase: number,
    op: number
  ) => {
    const x = cx + Math.sin(t * speed + phase) * 240;
    const y = cy + Math.cos(t * speed * 0.7 + phase) * 140;
    const scale = 1 + Math.sin(t * speed * 0.5 + phase) * 0.18;
    return (
      <div
        style={{
          position: "absolute",
          left: x - r,
          top: y - r,
          width: r * 2,
          height: r * 2,
          borderRadius: "50%",
          background: `radial-gradient(circle at 50% 50%, ${color} 0%, transparent 65%)`,
          filter: "blur(70px)",
          opacity: op * intensity,
          transform: `scale(${scale})`,
          mixBlendMode: "screen",
        }}
      />
    );
  };

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {blob(360, 380, 520, "rgba(196,164,132,0.85)", 0.18, 0.0, 0.85)}
      {blob(940, 320, 460, "rgba(166,139,111,0.8)", 0.13, 1.4, 0.7)}
      {blob(620, 540, 580, "rgba(120,100,80,0.9)", 0.10, 2.7, 0.85)}
      {blob(820, 200, 320, "rgba(220,200,170,0.55)", 0.22, 3.9, 0.5)}
    </AbsoluteFill>
  );
};

// ─── Grain noise overlay (SVG turbulence) ─────────────────────────
const GrainOverlay: React.FC<{ opacity?: number }> = ({ opacity = 0.16 }) => {
  const frame = useCurrentFrame();
  const seed = (frame % 8) + 1;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "overlay", opacity }}>
      <svg width="100%" height="100%">
        <filter id={`grain-${seed}`}>
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.9"
            numOctaves="2"
            stitchTiles="stitch"
            seed={seed}
          />
          <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.6 0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain-${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      pointerEvents: "none",
      background:
        "radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.45) 75%, rgba(0,0,0,0.85) 100%)",
    }}
  />
);

// ─── Letter drift (per-letter sin-wave bob) ───────────────────────
const Drifty: React.FC<{ text: string; baseDelay?: number; style?: React.CSSProperties }> = ({
  text,
  baseDelay = 0,
  style,
}) => {
  const frame = useCurrentFrame();
  return (
    <span style={{ display: "inline-flex", whiteSpace: "pre", ...style }}>
      {text.split("").map((ch, i) => {
        const t = (frame + baseDelay + i * 4) / FPS;
        const dy = Math.sin(t * 1.2) * 3;
        return (
          <span key={i} style={{ display: "inline-block", transform: `translateY(${dy}px)` }}>
            {ch === " " ? " " : ch}
          </span>
        );
      })}
    </span>
  );
};

// ─── Cold open (0:00–0:03) ────────────────────────────────────────
const ColdOpen: React.FC = () => {
  const frame = useCurrentFrame();
  const r = interpolate(frame, [0, 60, 90], [0, 240, 380], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });
  const op = interpolate(frame, [0, 30, 80], [0, 0.95, 0.55], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ background: INK }}>
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: r * 2,
            height: r * 2,
            borderRadius: "50%",
            background: `radial-gradient(circle, rgba(245,225,190,${op}) 0%, rgba(196,164,132,${op * 0.4}) 30%, transparent 70%)`,
            filter: "blur(40px)",
          }}
        />
      </AbsoluteFill>
      <GrainOverlay opacity={0.22} />
    </AbsoluteFill>
  );
};

// ─── Caption beat (italic serif text on drift fog) ────────────────
const CaptionBeat: React.FC<{
  children: React.ReactNode;
  totalFrames: number;
  overlay?: React.ReactNode;
  fogIntensity?: number;
  textWidthPct?: number;
}> = ({ children, totalFrames, overlay, fogIntensity = 1, textWidthPct = 70 }) => {
  const frame = useCurrentFrame();
  const opIn = interpolate(frame, [0, 18], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });
  const opOut = interpolate(frame, [totalFrames - 22, totalFrames - 4], [1, 0], {
    easing: Easing.in(Easing.cubic),
    extrapolateLeft: "clamp",
  });
  const op = Math.min(opIn, opOut);
  const blur = interpolate(opIn, [0, 1], [12, 0], { extrapolateRight: "clamp" });
  const ty = interpolate(opIn, [0, 1], [16, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: INK }}>
      <DriftFog intensity={fogIntensity} />
      {overlay}
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "0 8%" }}>
        <div
          style={{
            opacity: op,
            transform: `translateY(${ty}px)`,
            filter: `blur(${blur}px)`,
            fontFamily: "Fraunces, serif",
            fontStyle: "italic",
            fontWeight: 300,
            color: BONE,
            fontSize: 56,
            lineHeight: 1.2,
            letterSpacing: "-0.02em",
            textAlign: "center",
            maxWidth: `${textWidthPct}%`,
            textShadow: "0 4px 40px rgba(15,14,13,0.7)",
          }}
        >
          {children}
        </div>
      </AbsoluteFill>
      <GrainOverlay />
      <Vignette />
    </AbsoluteFill>
  );
};

const PresenceWord: React.FC<{ totalFrames: number }> = ({ totalFrames }) => {
  const frame = useCurrentFrame();
  const op = interpolate(
    frame,
    [10, 80, totalFrames - 50, totalFrames - 10],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const blur = interpolate(
    frame,
    [10, 90, totalFrames - 60, totalFrames - 5],
    [40, 0, 0, 50],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const scale = interpolate(frame, [0, totalFrames], [1.0, 1.06]);
  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          opacity: op * 0.92,
          filter: `blur(${blur}px)`,
          transform: `scale(${scale})`,
          fontFamily: "Anton, Impact, sans-serif",
          textTransform: "uppercase",
          color: BONE,
          fontSize: 240,
          letterSpacing: "-0.02em",
          lineHeight: 1,
          mixBlendMode: "screen",
        }}
      >
        Presence
      </div>
    </AbsoluteFill>
  );
};

const LightBeam: React.FC<{ totalFrames: number }> = ({ totalFrames }) => {
  const frame = useCurrentFrame();
  const op = interpolate(
    frame,
    [0, 30, totalFrames - 30, totalFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const sway = Math.sin(frame * 0.04) * 18;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: "50%",
          width: 220,
          height: "100%",
          transform: `translateX(${-110 + sway}px)`,
          background:
            "linear-gradient(180deg, rgba(245,225,190,0.0) 0%, rgba(245,225,190,0.55) 35%, rgba(245,225,190,0.55) 65%, rgba(245,225,190,0.0) 100%)",
          filter: "blur(35px)",
          opacity: op * 0.85,
          mixBlendMode: "screen",
        }}
      />
    </AbsoluteFill>
  );
};

const TitleCard: React.FC<{ totalFrames: number }> = ({ totalFrames }) => {
  const frame = useCurrentFrame();

  const dispOp = interpolate(frame, [10, 50], [0, 1], { extrapolateRight: "clamp" });
  const dispBlur = interpolate(frame, [10, 50], [25, 0], { extrapolateRight: "clamp" });
  const dispY = interpolate(frame, [10, 50], [40, 0], { extrapolateRight: "clamp" });

  const serifOp = interpolate(frame, [60, 110], [0, 1], { extrapolateRight: "clamp" });
  const serifBlur = interpolate(frame, [60, 110], [30, 0], { extrapolateRight: "clamp" });

  const lineOp = interpolate(frame, [110, 140], [0, 1], { extrapolateRight: "clamp" });
  const lineW = interpolate(frame, [110, 160], [0, 320], { extrapolateRight: "clamp" });

  const fadeOut = interpolate(
    frame,
    [totalFrames - 25, totalFrames - 4],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ background: INK }}>
      <DriftFog intensity={0.85} />
      <AbsoluteFill style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            opacity: dispOp * fadeOut,
            transform: `translateY(${dispY}px)`,
            filter: `blur(${dispBlur}px)`,
            fontFamily: "Anton, Impact, sans-serif",
            textTransform: "uppercase",
            color: BONE,
            fontSize: 200,
            letterSpacing: "-0.02em",
            lineHeight: 0.9,
            textAlign: "center",
            textShadow: "0 8px 60px rgba(196,164,132,0.45)",
          }}
        >
          Professional<br />Drift
        </div>

        <div
          style={{
            marginTop: 28,
            opacity: serifOp * fadeOut,
            filter: `blur(${serifBlur}px)`,
            fontFamily: "Fraunces, serif",
            fontStyle: "italic",
            fontWeight: 300,
            color: PRIMARY,
            fontSize: 78,
            letterSpacing: "-0.02em",
            lineHeight: 1,
          }}
        >
          The Quiet Line.
        </div>

        <div
          style={{
            marginTop: 38,
            opacity: lineOp * fadeOut,
            width: lineW,
            height: 1,
            background: PRIMARY,
          }}
        />
      </AbsoluteFill>
      <GrainOverlay />
      <Vignette />
    </AbsoluteFill>
  );
};

const Byline: React.FC<{ totalFrames: number }> = ({ totalFrames }) => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [0, 18, totalFrames - 6, totalFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cursorOp = (Math.floor(frame / 12) % 2 === 0) ? 1 : 0;
  return (
    <AbsoluteFill style={{ background: INK }}>
      <DriftFog intensity={0.6} />
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            opacity: op,
            fontFamily: "Inter, sans-serif",
            fontWeight: 700,
            fontSize: 22,
            letterSpacing: "0.45em",
            textTransform: "uppercase",
            color: PRIMARY,
            textAlign: "center",
          }}
        >
          A Lecture by Tristian Walker
          <span style={{ display: "inline-block", marginLeft: 8, opacity: cursorOp, color: BONE }}>|</span>
        </div>
      </AbsoluteFill>
      <GrainOverlay />
      <Vignette />
    </AbsoluteFill>
  );
};

export const MyComposition: React.FC = () => {
  useFonts();
  const { fps } = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);

  return (
    <AbsoluteFill style={{ background: INK, fontKerning: "normal" }}>
      <Sequence from={0} durationInFrames={f(3)}>
        <ColdOpen />
      </Sequence>

      <Sequence from={f(3)} durationInFrames={f(5)}>
        <CaptionBeat totalFrames={f(5)}>
          In every interaction<span style={{ color: PRIMARY }}>…</span>
        </CaptionBeat>
      </Sequence>

      <Sequence from={f(8)} durationInFrames={f(5)}>
        <CaptionBeat totalFrames={f(5)}>
          <span style={{ color: BONE }}>…there is a </span>
          <Drifty text="quiet line" style={{ color: PRIMARY }} />
          <span style={{ color: BONE }}>.</span>
        </CaptionBeat>
      </Sequence>

      <Sequence from={f(13)} durationInFrames={f(7)}>
        <CaptionBeat totalFrames={f(7)} textWidthPct={62}>
          It is the line between{" "}
          <span style={{ color: PRIMARY, fontStyle: "italic" }}>presence</span>{" "}
          and{" "}
          <span style={{ color: PRIMARY_DEEP, fontStyle: "italic" }}>process</span>.
        </CaptionBeat>
      </Sequence>

      <Sequence from={f(20)} durationInFrames={f(8)}>
        <CaptionBeat
          totalFrames={f(8)}
          fogIntensity={0.7}
          overlay={<PresenceWord totalFrames={f(8)} />}
        >
          When the task overrules the human,{" "}
          <span style={{ color: PRIMARY }}>character drifts</span>.
        </CaptionBeat>
      </Sequence>

      <Sequence from={f(28)} durationInFrames={f(6)}>
        <CaptionBeat
          totalFrames={f(6)}
          fogIntensity={0.85}
          overlay={<LightBeam totalFrames={f(6)} />}
        >
          Most never notice it.<br />
          <span style={{ color: PRIMARY }}>The few who do<span style={{ color: PRIMARY }}>…</span></span>
        </CaptionBeat>
      </Sequence>

      <Sequence from={f(34)} durationInFrames={f(9)}>
        <TitleCard totalFrames={f(9)} />
      </Sequence>

      <Sequence from={f(43)} durationInFrames={f(2)}>
        <Byline totalFrames={f(2)} />
      </Sequence>

      <Audio src={staticFile("audio.mp3")} />
    </AbsoluteFill>
  );
};
