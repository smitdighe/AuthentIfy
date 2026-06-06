/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        auth: {
          bg: '#192837',
          accent: '#0ea5e9',
          silver: '#0ea5e9',
          muted: 'rgba(14,165,233,0.5)',
          surface: 'rgba(14,165,233,0.05)',
          border: 'rgba(14,165,233,0.15)',
        },
        verdict: {
          genuine: '#0ea5e9',
          suspicious: '#ffff00',
          tampered: '#ff0000',
        },
      },
      fontFamily: {
        heading: ['Helvetica Now Display Bold', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        accent: '0 4px 24px rgba(14,165,233,0.28)',
        card: '0 8px 32px rgba(17, 49, 64, 0.6)',
        glow: '0 0 40px rgba(14,165,233,0.15)',
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