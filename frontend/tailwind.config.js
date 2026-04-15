/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Cyberpunk Dark Theme
        cyber: {
          bg: '#020408',
          bg2: '#050d12',
          surface: '#080e14',
          surface2: '#0d1a24',
          surface3: '#112030',
          border: '#1a3040',
          border2: '#1e3f55',
        },
        // Neon Colors
        neon: {
          green: '#00ff88',
          green2: '#00cc6a',
          cyan: '#00d8ff',
          cyan2: '#00b8d9',
          blue: '#0066ff',
          purple: '#7c3aed',
          pink: '#ff00ff',
          red: '#ff2244',
          yellow: '#ffcc00',
          orange: '#ff6600',
        },
        // Text Colors
        text: {
          primary: '#b8d4e8',
          secondary: '#7a9cb8',
          muted: '#3a5568',
          dim: '#1e3040',
        }
      },
      fontFamily: {
        mono: ['"IBM Plex Mono"', 'monospace'],
        arabic: ['Cairo', 'sans-serif'],
      },
      animation: {
        // Glow animations
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'glow-cyan': 'glow-cyan 2s ease-in-out infinite',
        'glow-green': 'glow-green 2s ease-in-out infinite',
        // Border animations
        'border-flow': 'border-flow 4s linear infinite',
        // Grid animation
        'grid-drift': 'grid-drift 20s linear infinite',
        // Float animation
        'float': 'float 6s ease-in-out infinite',
        // Scan line
        'scan': 'scan 4s linear infinite',
        // Glitch
        'glitch': 'glitch 1s linear infinite',
        // Pulse
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        // Shine
        'shine': 'shine 3s ease-in-out infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 255, 136, 0.4), 0 0 60px rgba(0, 255, 136, 0.1)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 255, 136, 0.6), 0 0 80px rgba(0, 255, 136, 0.2)' },
        },
        'glow-cyan': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 216, 255, 0.4), 0 0 60px rgba(0, 216, 255, 0.1)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 216, 255, 0.6), 0 0 80px rgba(0, 216, 255, 0.2)' },
        },
        'glow-green': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 255, 136, 0.4)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 255, 136, 0.6)' },
        },
        'border-flow': {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '50%': { opacity: '1' },
          '100%': { transform: 'translateY(100%)', opacity: '0' },
        },
        'grid-drift': {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '50px 50px' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'scan': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        'glitch': {
          '0%, 100%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 2px)' },
          '40%': { transform: 'translate(-2px, -2px)' },
          '60%': { transform: 'translate(2px, 2px)' },
          '80%': { transform: 'translate(2px, -2px)' },
        },
        'shine': {
          '0%, 100%': { transform: 'translateX(-100%)' },
          '50%': { transform: 'translateX(100%)' },
        },
      },
      backgroundImage: {
        'cyber-gradient': 'linear-gradient(135deg, #00d8ff 0%, #00ff88 100%)',
        'neon-gradient': 'linear-gradient(135deg, #00ff88 0%, #00d8ff 50%, #7c3aed 100%)',
        'grid-pattern': 'linear-gradient(rgba(0, 255, 136, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 136, 0.03) 1px, transparent 1px)',
      },
      boxShadow: {
        'neon-green': '0 0 20px rgba(0, 255, 136, 0.4), 0 0 60px rgba(0, 255, 136, 0.1)',
        'neon-cyan': '0 0 20px rgba(0, 216, 255, 0.4), 0 0 60px rgba(0, 216, 255, 0.1)',
        'neon-purple': '0 0 20px rgba(124, 58, 237, 0.4), 0 0 60px rgba(124, 58, 237, 0.1)',
        'neon-red': '0 0 20px rgba(255, 34, 68, 0.4), 0 0 60px rgba(255, 34, 68, 0.1)',
        'card': '0 8px 40px rgba(0, 0, 0, 0.4), 0 0 30px rgba(0, 216, 255, 0.06)',
        'card-hover': '0 12px 50px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 216, 255, 0.1)',
      },
    },
  },
  plugins: [],
}
