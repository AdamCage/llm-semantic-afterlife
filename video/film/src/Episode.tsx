import React from "react";
import {
  AbsoluteFill,
  CanvasImage,
  Html5Audio,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import data from "./episode.generated.json";

type Scene = (typeof data.scenes)[number];
const C = {
  bg: "#081321",
  ink: "#f5f5f0",
  muted: "#a2b6c9",
  blue: data.palette[5],
  amber: data.palette[4],
  green: data.palette[2],
  red: data.palette[1],
};
const ease = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};
const font = "'Segoe UI', Arial, sans-serif";

const Entrance: React.FC<
  React.PropsWithChildren<{ delay?: number; style?: React.CSSProperties }>
> = ({ children, delay = 0, style }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div
      style={{
        opacity: interpolate(
          f,
          [delay * fps, (delay + 0.7) * fps],
          [0, 1],
          ease,
        ),
        translate: `0 ${interpolate(f, [delay * fps, (delay + 0.7) * fps], [20, 0], ease)}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

const Background = () => (
  <AbsoluteFill style={{ background: C.bg }}>
    <svg width="1920" height="1080" style={{ opacity: 0.13 }}>
      <defs>
        <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1.4" fill={C.blue} />
        </pattern>
        <radialGradient id="wash">
          <stop stopColor="#1a4567" />
          <stop offset="1" stopColor={C.bg} />
        </radialGradient>
      </defs>
      <rect width="1920" height="1080" fill="url(#wash)" />
      <rect width="1920" height="1080" fill="url(#grid)" />
    </svg>
  </AbsoluteFill>
);

const Footer: React.FC<{ scene: Scene }> = ({ scene }) => {
  const f = useCurrentFrame();
  const empirical = ["gap", "family_gap", "completion", "escape"].includes(
    scene.visual,
  );
  return (
    <>
      <div
        style={{
          position: "absolute",
          left: 112,
          bottom: 65,
          right: 112,
          display: "flex",
          justifyContent: "space-between",
          fontSize: 22,
          color: C.muted,
        }}
      >
        <span>
          {empirical
            ? "ДАННЫЕ ИССЛЕДОВАНИЯ · источники в описании"
            : scene.visual === "hero" || scene.visual === "loop"
              ? "ИИ-ИЛЛЮСТРАЦИЯ · художественная метафора"
              : "ОБЪЯСНЯЮЩАЯ СХЕМА · не экспериментальные данные"}
        </span>
        <span>SEMANTIC AFTERLIFE / {scene.id}</span>
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 0,
          height: 4,
          left: 0,
          width: `${((scene.from + f) / data.duration) * 100}%`,
          background: C.blue,
          opacity: 0.6,
        }}
      />
    </>
  );
};

const Cards: React.FC<{ scene: Scene }> = ({ scene }) => (
  <div
    style={{ display: "flex", gap: 28, alignItems: "stretch", minHeight: 335 }}
  >
    {scene.lines.map((line, i) => (
      <Entrance
        key={line}
        delay={1 + i * 4}
        style={{
          flex: 1,
          borderTop: `3px solid ${[C.blue, C.amber, C.green, C.blue][i]}`,
          padding: "34px 30px",
          background: "#102436",
          borderRadius: 14,
        }}
      >
        <div
          style={{
            fontSize: 27,
            letterSpacing: 4,
            color: C.muted,
            marginBottom: 42,
          }}
        >
          0{i + 1}
        </div>
        <div style={{ fontSize: 45, lineHeight: 1.25, fontWeight: 500 }}>
          {line}
        </div>
      </Entrance>
    ))}
  </div>
);

const WindowDiagram = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(f, [2 * fps, 22 * fps], [0, 1], ease);
  const shift = Math.floor(p * 12);
  return (
    <div>
      <svg viewBox="0 0 1640 440" style={{ width: "100%" }}>
        <defs>
          <clipPath id="tail">
            <rect x="220" y="100" width="1190" height="150" rx="18" />
          </clipPath>
        </defs>
        <text x="220" y="55" fill={C.blue} fontSize="32">
          Модель видит только это окно
        </text>
        <rect
          x="220"
          y="100"
          width="1190"
          height="150"
          rx="18"
          fill="#122c41"
          stroke={C.blue}
          strokeWidth="3"
        />
        <g clipPath="url(#tail)">
          {Array.from({ length: 28 }, (_, i) => (
            <g key={i} transform={`translate(${238 + (i - shift) * 96},120)`}>
              <rect
                width="80"
                height="110"
                rx="8"
                fill={i < 10 ? C.amber : C.blue}
                opacity="0.8"
              />
              <path
                d="M16 35h48M16 53h38M16 71h44"
                stroke={C.bg}
                strokeWidth="5"
                opacity="0.55"
              />
            </g>
          ))}
        </g>
        <text x="220" y="305" fill={C.amber} fontSize="30">
          Исходный текст
        </text>
        <text x="1030" y="305" fill={C.blue} fontSize="30">
          Новые токены
        </text>
        <path
          d="M340 360H1290m-25-20 25 20-25 20"
          stroke={C.muted}
          fill="none"
          strokeWidth="3"
        />
      </svg>
      <Entrance
        delay={22}
        style={{ textAlign: "center", fontSize: 42, color: C.amber }}
      >
        Прямого доступа к исходному тексту больше нет
      </Entrance>
    </div>
  );
};

const Protocol: React.FC<{ scene: Scene }> = ({ scene }) => (
  <div>
    <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
      {scene.lines.map((line, i) => (
        <React.Fragment key={line}>
          <Entrance
            delay={i * 3}
            style={{
              flex: 1,
              padding: "42px 26px",
              border: `2px solid ${i === 1 ? C.amber : C.blue}`,
              borderRadius: 18,
              fontSize: 40,
              lineHeight: 1.25,
              minHeight: 210,
              display: "flex",
              alignItems: "center",
            }}
          >
            {line}
          </Entrance>
          {i < scene.lines.length - 1 && (
            <span style={{ fontSize: 55, color: C.muted }}>→</span>
          )}
        </React.Fragment>
      ))}
    </div>
    <Entrance
      delay={12}
      style={{
        marginTop: 60,
        textAlign: "center",
        fontSize: 38,
        color: C.muted,
      }}
    >
      {scene.id === "04"
        ? "P1: повторные запросы из последнего хвоста"
        : "Инженерные направления для проверки"}
    </Entrance>
  </div>
);

const Gap = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div>
      <div style={{ fontSize: 36, color: C.muted, marginBottom: 20 }}>
        Последняя полоса · независимая репликация · 95% интервалы
      </div>
      <svg viewBox="0 0 1640 400" style={{ width: "100%" }}>
        {data.replication.map((r, i) => {
          const y = 65 + i * 120;
          const factor = interpolate(
            f,
            [(2 + i * 3) * fps, (3 + i * 3) * fps],
            [0, 1],
            ease,
          );
          const x = (v: number) => 600 + v * 1270;
          return (
            <g key={r.embedding} opacity={factor}>
              <text x="0" y={y + 10} fill={C.ink} fontSize="34">
                {r.embedding}
              </text>
              <line
                x1="600"
                x2="1500"
                y1={y}
                y2={y}
                stroke="#30485c"
                strokeWidth="2"
              />
              <line
                x1={x(r.gap_ci_low)}
                x2={x(r.gap_ci_high)}
                y1={y}
                y2={y}
                stroke={C.blue}
                strokeWidth="6"
              />
              <line
                x1={x(r.gap_ci_low)}
                x2={x(r.gap_ci_low)}
                y1={y - 12}
                y2={y + 12}
                stroke={C.blue}
                strokeWidth="3"
              />
              <line
                x1={x(r.gap_ci_high)}
                x2={x(r.gap_ci_high)}
                y1={y - 12}
                y2={y + 12}
                stroke={C.blue}
                strokeWidth="3"
              />
              <circle cx={x(r.gap)} cy={y} r="10" fill={C.blue} />
              <text
                x={x(r.gap)}
                y={y + 49}
                textAnchor="middle"
                fontSize="27"
                fill={C.muted}
              >
                {r.gap.toFixed(3)} [{r.gap_ci_low.toFixed(3)};{" "}
                {r.gap_ci_high.toFixed(3)}]
              </text>
            </g>
          );
        })}
      </svg>
      <div style={{ fontSize: 31, color: C.amber }}>
        G = D между началами − D внутри начала
      </div>
      <div style={{ fontSize: 27, color: C.muted, marginTop: 14 }}>
        Косинусный контраст. Пространства не объединяются. Пропуски не
        заполнены.
      </div>
    </div>
  );
};

const Completion = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const families = ["Qwen3-8B", "OLMo-3-7B", "Ministral-3-8B", "Gemma-4-12B"];
  const seconds = f / fps;
  const idx = seconds < 7 ? 0 : seconds < 12 ? 2 : seconds < 18 ? 1 : 3;
  const family = families[idx];
  const rows = data.completion.filter(
    (r) => r.family === family && r.quantization === "nf4",
  );
  return (
    <div>
      <div style={{ display: "flex", gap: 38, marginBottom: 40 }}>
        {families.map((name, i) => (
          <span
            key={name}
            style={{
              fontSize: 29,
              color: idx === i ? C.blue : C.muted,
              borderBottom:
                idx === i ? `2px solid ${C.blue}` : "2px solid transparent",
              paddingBottom: 10,
            }}
          >
            {name}
          </span>
        ))}
      </div>
      <div style={{ fontSize: 26, color: C.muted, marginBottom: 18 }}>
        Достигли целевой длины / запланированные запуски · NF4 · P1 · 12W
      </div>
      {rows.map((r, i) => (
        <div
          key={r.checkpoint}
          style={{ display: "flex", gap: 25, alignItems: "center", height: 92 }}
        >
          <span style={{ width: 270, fontSize: 33 }}>
            {r.checkpoint.replace(" NF4", "")}
          </span>
          <div
            style={{
              height: 42,
              width: 900,
              background: "#203344",
              borderRadius: 8,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${(r.n_completed / r.n_planned) * 100}%`,
                background: [C.blue, C.green, C.amber, C.red][i],
              }}
            />
          </div>
          <span style={{ fontSize: 37, color: C.ink }}>
            {r.n_completed}/{r.n_planned}
          </span>
        </div>
      ))}
      <div style={{ fontSize: 28, color: C.amber, marginTop: 26 }}>
        Это стрессовый протокол, не рейтинг качества ответов.
      </div>
    </div>
  );
};

const FamilyGap = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const families = ["Qwen3-8B", "OLMo-3-7B", "Ministral-3-8B", "Gemma-4-12B"];
  const seconds = f / fps;
  const index = seconds < 5 ? 0 : seconds < 11 ? 2 : 3;
  const family = families[index];
  const rows = data.familyGap.filter(
    (r) => r.family === family && r.quantization === "nf4",
  );
  const spaces = ["BGE-M3", "Qwen3-Embedding-8B"];
  return (
    <div>
      <div style={{ fontSize: 39, color: C.blue, marginBottom: 18 }}>
        {family} · последняя полоса · NF4 · 12W
      </div>
      <svg viewBox="0 0 1640 390" style={{ width: "100%" }}>
        {spaces.map((space, k) => {
          const offset = k * 820;
          const selected = rows.filter((r) => r.space === space);
          const x = (v: number) => offset + 320 + (v + 0.2) * 760;
          return (
            <g key={space}>
              <text x={offset + 15} y="36" fill={C.muted} fontSize="28">
                {space}
              </text>
              <line
                x1={x(0)}
                x2={x(0)}
                y1="70"
                y2="340"
                stroke={C.muted}
                strokeDasharray="7 7"
              />
              {selected.map((r, i) => {
                const y = 100 + i * 66;
                const v = r.last_band_G as number | null;
                const lo = r.G_lo as number | null;
                const hi = r.G_hi as number | null;
                return (
                  <g key={r.checkpoint}>
                    <text x={offset + 15} y={y + 9} fill={C.ink} fontSize="29">
                      {r.checkpoint.replace(" NF4", "")}
                    </text>
                    {v !== null && lo !== null && hi !== null ? (
                      <>
                        <line
                          x1={x(lo)}
                          x2={x(hi)}
                          y1={y}
                          y2={y}
                          stroke={C.blue}
                          strokeWidth="4"
                        />
                        <circle
                          cx={x(v)}
                          cy={y}
                          r="8"
                          fill={r.ci_excludes_0 ? C.blue : C.bg}
                          stroke={C.blue}
                          strokeWidth="3"
                        />
                      </>
                    ) : (
                      <text
                        x={offset + 365}
                        y={y + 8}
                        fill={C.muted}
                        fontSize="26"
                      >
                        нет оценки
                      </text>
                    )}
                  </g>
                );
              })}
              {[-0.2, 0, 0.2, 0.4].map((v) => (
                <text
                  key={v}
                  x={x(v)}
                  y="375"
                  fill={C.muted}
                  fontSize="24"
                  textAnchor="middle"
                >
                  {v.toFixed(1)}
                </text>
              ))}
            </g>
          );
        })}
      </svg>
      <div style={{ fontSize: 27, color: C.muted }}>
        G — косинусный контраст. Опубликованные интервалы. Пространства не
        объединяются.
      </div>
      <div style={{ fontSize: 28, color: C.amber, marginTop: 15 }}>
        Пустой маркер: интервал включает 0. Пропуск: нет определённой оценки.
      </div>
    </div>
  );
};

const Escape = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = interpolate(f, [2 * fps, 12 * fps], [0, 1], ease);
  return (
    <div style={{ display: "flex", gap: 65 }}>
      <div style={{ width: 450 }}>
        <div style={{ fontSize: 140, color: C.amber, lineHeight: 1 }}>
          0 / 8
        </div>
        <div style={{ fontSize: 37, lineHeight: 1.25, marginTop: 26 }}>
          подтверждённых выходов до границы наблюдения
        </div>
        <div style={{ fontSize: 28, color: C.muted, marginTop: 34 }}>
          Выбранные петли
          <br />
          P1 · NF4 · T = 0,3
          <br />W = 4096
        </div>
      </div>
      <svg viewBox="0 0 1040 505" style={{ width: 1040 }}>
        {data.escape.map((r, i) => {
          const y = 45 + i * 48;
          const end = 200 + progress * 760;
          return (
            <g key={i}>
              <text x="0" y={y + 8} fill={C.muted} fontSize="22">
                {String(r.cell)}
              </text>
              <line
                x1="200"
                x2={end}
                y1={y}
                y2={y}
                stroke={i < 4 ? C.blue : C.green}
                strokeWidth="4"
              />
              <line
                x1={end}
                x2={end}
                y1={y - 9}
                y2={y + 9}
                stroke={i < 4 ? C.blue : C.green}
                strokeWidth="3"
              />
            </g>
          );
        })}
        <line
          x1="960"
          x2="960"
          y1="15"
          y2="405"
          stroke={C.muted}
          strokeDasharray="6 8"
        />
        <text x="200" y="450" fill={C.muted} fontSize="25">
          0
        </text>
        <text x="960" y="450" textAnchor="end" fill={C.ink} fontSize="28">
          4 999 168 токенов
        </text>
        <text x="200" y="494" fill={C.muted} fontSize="23">
          От начала серии; справа — цензурирование, не выход
        </text>
      </svg>
    </div>
  );
};

const Twins = () => (
  <div>
    <div style={{ display: "flex", gap: 36 }}>
      {["Исходная ситуация A", "Контрфактическая ситуация B"].map(
        (title, i) => (
          <Entrance
            key={title}
            delay={i * 3}
            style={{
              flex: 1,
              border: `2px solid ${i ? C.amber : C.blue}`,
              padding: 38,
              borderRadius: 20,
            }}
          >
            <div style={{ fontSize: 37, marginBottom: 45 }}>{title}</div>
            <div style={{ color: C.muted, fontSize: 37 }}>
              Техническая тема →<br />
              технический словарь →<br />
              технический словарь…
            </div>
          </Entrance>
        ),
      )}
    </div>
    <Entrance
      delay={14}
      style={{
        fontSize: 43,
        color: C.amber,
        textAlign: "center",
        marginTop: 45,
      }}
    >
      Сохранилась ли разница между A и B?
    </Entrance>
  </div>
);

const Quote = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const index = Math.floor(f / (6 * fps)) % 3;
  return (
    <div>
      <div
        style={{
          color: C.amber,
          fontSize: 30,
          letterSpacing: 3,
          marginBottom: 35,
        }}
      >
        {["РАННИЙ ФРАГМЕНТ", "СЕРЕДИНА", "ПОЗДНИЙ ФРАГМЕНТ"][index]} · MINISTRAL
        / mb-physics-s1
      </div>
      <div
        style={{
          fontSize: 56,
          lineHeight: 1.45,
          maxWidth: 1500,
          fontFamily: "Georgia, serif",
        }}
      >
        “The Polyakov loop is zero, and the configurations are generated with a
        Metropolis algorithm…”
      </div>
      <div style={{ fontSize: 28, color: C.muted, marginTop: 50 }}>
        Сокращённая цитата вывода модели, не утверждение о физике.
        <br />
        Пример одного продолжения; не обобщение на все восемь.
      </div>
    </div>
  );
};

const Hero: React.FC<{ scene: Scene }> = ({ scene }) => {
  const f = useCurrentFrame();
  return (
    <>
      <CanvasImage
        src={staticFile(scene.asset || "afterglow.png")}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          objectFit: "cover",
          scale: interpolate(f, [0, scene.duration], [1, 1.045], ease),
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(90deg, rgba(5,14,26,.97), rgba(5,14,26,.72) 48%, rgba(5,14,26,.1))",
        }}
      />
      <div
        style={{ position: "absolute", left: 112, top: 140, maxWidth: 1110 }}
      >
        <Entrance>
          <div
            style={{
              fontSize: 28,
              color: C.blue,
              letterSpacing: 5,
              textTransform: "uppercase",
              marginBottom: 42,
            }}
          >
            {scene.chapter} / SEMANTIC AFTERLIFE
          </div>
          <div
            style={{
              fontSize: scene.id === "01" ? 112 : 90,
              lineHeight: 1.07,
              fontWeight: 600,
              letterSpacing: -3,
            }}
          >
            {scene.title}
          </div>
        </Entrance>
        <div style={{ marginTop: 65 }}>
          {scene.lines.map((line, i) => (
            <Entrance
              key={line}
              delay={4 + i * 6}
              style={{
                fontSize: 37,
                lineHeight: 1.3,
                color: i === 0 ? C.ink : C.muted,
                marginBottom: 25,
              }}
            >
              {line}
            </Entrance>
          ))}
        </div>
      </div>
    </>
  );
};

const Content: React.FC<{ scene: Scene }> = ({ scene }) => {
  switch (scene.visual) {
    case "window":
      return <WindowDiagram />;
    case "protocol":
      return <Protocol scene={scene} />;
    case "gap":
      return <Gap />;
    case "completion":
      return <Completion />;
    case "family_gap":
      return <FamilyGap />;
    case "escape":
      return <Escape />;
    case "twins":
      return <Twins />;
    case "quote":
      return <Quote />;
    default:
      return <Cards scene={scene} />;
  }
};

const SceneView: React.FC<{ scene: Scene }> = ({ scene }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const hero = scene.visual === "hero" || scene.visual === "loop";
  return (
    <AbsoluteFill
      style={{
        fontFamily: font,
        color: C.ink,
        opacity: interpolate(
          f,
          [0, 0.6 * fps, scene.duration - 0.5 * fps, scene.duration - 1],
          [0, 1, 1, 0],
          ease,
        ),
      }}
    >
      <Background />
      {hero ? (
        <Hero scene={scene} />
      ) : (
        <>
          <div style={{ position: "absolute", left: 112, right: 112, top: 80 }}>
            <Entrance>
              <div
                style={{
                  fontSize: 27,
                  letterSpacing: 5,
                  color: C.blue,
                  textTransform: "uppercase",
                  marginBottom: 27,
                }}
              >
                {scene.chapter} / {scene.id}
              </div>
              <div
                style={{
                  fontSize: 80,
                  lineHeight: 1.12,
                  fontWeight: 600,
                  letterSpacing: -2,
                }}
              >
                {scene.title}
              </div>
            </Entrance>
          </div>
          <div
            style={{
              position: "absolute",
              left: 112,
              right: 112,
              top: 330,
              bottom: 150,
            }}
          >
            <Content scene={scene} />
          </div>
        </>
      )}
      <Footer scene={scene} />
      {scene.voiceReady && (
        <Sequence from={scene.lead} layout="none">
          <Html5Audio src={staticFile(`voice/${scene.id}.mp3`)} />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};

export const Episode: React.FC = () => (
  <AbsoluteFill style={{ background: C.bg }}>
    {data.scenes.map((scene) => (
      <Sequence
        key={scene.id}
        name={`${scene.id} ${scene.title}`}
        from={scene.from}
        durationInFrames={scene.duration}
      >
        <SceneView scene={scene} />
      </Sequence>
    ))}
    <Html5Audio src={staticFile("score.mp3")} />
  </AbsoluteFill>
);
