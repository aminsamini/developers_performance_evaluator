/** @type {import('tailwindcss').Config} */
import animate from 'tailwindcss-animate'

export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    animate,
  ],
}
