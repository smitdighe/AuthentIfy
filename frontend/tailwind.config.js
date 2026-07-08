/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        auth: {
          bg: '#0a0a0b',
          text: '#e5e5e5',
          accent: '#f59e0b',
          silver: '#e5e5e5',
          muted: 'rgba(229,229,229,0.5)',
          surface: 'rgba(18,18,20,0.5)',
          border: 'rgba(245,158,11,0.15)',
        },
        verdict: {
          genuine: '#3fae6a',
          suspicious: '#d9a441',
          tampered: '#d95a5a',
        },
      },
      fontFamily: {
        heading: ['Helvetica Now Display Bold', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        accent: '0 0 20px rgba(245,158,11,0.25)',
        card: '0 8px 32px rgba(0, 0, 0, 0.6)',
        glow: '0 0 20px rgba(245,158,11,0.25)',
      },
      animation: {
        fadeUp: 'fadeUp 0.6s ease forwards',
        fadeIn: 'fadeIn 0.4s ease forwards',
        'pulse-slow': 'pulse 3s infinite',
        scan: 'scan 2s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(28px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scan: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(8px)' },
        },
      },
    },
  },
  plugins: [],
};