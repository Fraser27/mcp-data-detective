/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f7ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        secondary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        detective: {
          50: '#f5f5f5',
          100: '#e9e9e9',
          200: '#d9d9d9',
          300: '#a3a3a3',
          400: '#737373',
          500: '#525252',
          600: '#404040',
          700: '#262626',
          800: '#171717',
          900: '#0a0a0a',
          accent: '#fbbf24', // Detective's magnifying glass gold accent
          clue: '#ef4444',    // Clue highlight red
          paper: '#f3f4f6',   // Old paper background
          ink: '#1f2937',     // Ink color for detective notes
        }
      },
      backgroundImage: {
        'detective-pattern': "url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMxMTExMTEiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PHBhdGggZD0iTTM2IDM0aDR2MWgtNHYtMXptMC0yaDF2NWgtMXYtNXptMi0yaDF2NGgtMXYtNHptLTIgMmgtMXYxaDJ2LTFoLTF6bS0yLTJoNXYxaC01di0xem0yLTJoMXY1aC0xdi01eiIvPjwvZz48L2c+PC9zdmc+');",
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'magnify': 'magnify 2s ease-in-out infinite',
        'pipe-glow': 'pipeGlow 2s ease-in-out infinite',
        'smoke-1': 'smoke1 3s infinite',
        'smoke-2': 'smoke2 3s infinite 1s',
        'smoke-3': 'smoke3 3s infinite 2s',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        magnify: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
        },
        pipeGlow: {
          '0%, 100%': { filter: 'drop-shadow(0 0 2px rgba(251, 191, 36, 0.3))' },
          '50%': { filter: 'drop-shadow(0 0 5px rgba(251, 191, 36, 0.6))' },
        },
        smoke1: {
          '0%': { transform: 'translateY(0) scale(0.8)', opacity: '0.8' },
          '100%': { transform: 'translateY(-20px) scale(1.5)', opacity: '0' },
        },
        smoke2: {
          '0%': { transform: 'translateY(0) scale(0.5)', opacity: '0' },
          '20%': { opacity: '0.6' },
          '100%': { transform: 'translateY(-15px) scale(1.2)', opacity: '0' },
        },
        smoke3: {
          '0%': { transform: 'translateY(0) scale(0.7)', opacity: '0' },
          '40%': { opacity: '0.7' },
          '100%': { transform: 'translateY(-25px) scale(1.3)', opacity: '0' },
        }
      },
      boxShadow: {
        'detective': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06), inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
      }
    },
  },
  plugins: [],
} 