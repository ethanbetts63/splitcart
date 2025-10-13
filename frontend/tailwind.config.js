/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: 'hsl(226.2, 57%, 21%)',
        foreground: 'hsl(213.8, 100%, 96.9%)',
        card: 'white',
        'card-foreground': 'hsl(226.2, 57%, 21%)',
        popover: 'hsl(214.3, 94.6%, 92.7%)',
        'popover-foreground': 'hsl(226.2, 57%, 21%)',
        primary: 'hsl(221.2, 83.2%, 53.3%)',
        'primary-foreground': 'hsl(213.8, 100%, 96.9%)',
        secondary: 'hsl(213.1, 93.9%, 67.8%)',
        'secondary-foreground': 'hsl(226.2, 57%, 21%)',
        muted: 'hsl(211.7, 96.4%, 78.4%)',
        'muted-foreground': 'hsl(224.3, 76.3%, 48%)',
        accent: 'hsl(213.3, 96.9%, 87.3%)',
        'accent-foreground': 'hsl(226.2, 57%, 21%)',
        border: 'hsl(213.3, 96.9%, 87.3%)',
        input: 'hsl(214.3, 94.6%, 92.7%)',
        ring: 'hsl(221.2, 83.2%, 53.3%)',
      },
    },
  },
  plugins: [],
}