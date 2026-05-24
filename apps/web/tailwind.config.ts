import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        bg: 'rgb(var(--bg) / <alpha-value>)',
        elevated: 'rgb(var(--bg-elevated) / <alpha-value>)',
        muted: 'rgb(var(--bg-muted) / <alpha-value>)',
        ink: 'rgb(var(--text) / <alpha-value>)',
        subtle: 'rgb(var(--text-muted) / <alpha-value>)',
        soft: 'rgb(var(--text-soft) / <alpha-value>)',
        brand: {
          DEFAULT: 'rgb(var(--primary) / <alpha-value>)',
          hover: 'rgb(var(--primary-hover) / <alpha-value>)',
        },
        teal: 'rgb(var(--secondary) / <alpha-value>)',
        violet: 'rgb(var(--accent) / <alpha-value>)',
        line: 'rgb(var(--border) / <alpha-value>)',
        success: 'rgb(var(--success) / <alpha-value>)',
        warning: 'rgb(var(--warning) / <alpha-value>)',
        danger: 'rgb(var(--danger) / <alpha-value>)',
      },
      boxShadow: {
        soft: '0 18px 45px rgba(15, 23, 42, 0.08)',
        card: '0 12px 30px rgba(15, 23, 42, 0.07)',
        lift: '0 24px 60px rgba(15, 23, 42, 0.12)',
      },
      borderRadius: {
        xl: '18px',
        '2xl': '24px',
        '3xl': '32px',
      },
      keyframes: {
        float: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } },
        shimmer: { '0%': { backgroundPosition: '0% 50%' }, '100%': { backgroundPosition: '100% 50%' } },
      },
      animation: {
        float: 'float 7s ease-in-out infinite',
        shimmer: 'shimmer 7s linear infinite alternate',
      },
    },
  },
  plugins: [],
};
export default config;
