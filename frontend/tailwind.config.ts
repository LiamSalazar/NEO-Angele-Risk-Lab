import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "IBM Plex Mono", "ui-monospace", "monospace"]
      },
      colors: {
        void: "#03070f",
        hull: "#07111f",
        console: "#0b1728",
        cyan: {
          signal: "#42f2ff",
          muted: "#66c9d6"
        },
        amber: {
          signal: "#f7c75f"
        },
        ion: "#8ff0c1",
        danger: "#ff5d73"
      },
      boxShadow: {
        "console-glow": "0 0 0 1px rgba(66, 242, 255, 0.14), 0 18px 80px rgba(0, 0, 0, 0.45)",
        "risk-glow": "0 0 34px rgba(66, 242, 255, 0.18)"
      },
      backgroundImage: {
        "console-grid":
          "linear-gradient(rgba(80, 210, 230, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(80, 210, 230, 0.04) 1px, transparent 1px)"
      },
      keyframes: {
        beacon: {
          "0%, 100%": { opacity: "0.25", transform: "scale(0.88)" },
          "50%": { opacity: "1", transform: "scale(1.12)" }
        },
        sweep: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" }
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" }
        }
      },
      animation: {
        beacon: "beacon 2.4s ease-in-out infinite",
        sweep: "sweep 8s linear infinite",
        scan: "scan 3.8s linear infinite"
      }
    }
  },
  plugins: []
};

export default config;
