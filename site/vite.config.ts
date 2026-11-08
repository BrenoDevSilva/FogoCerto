import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' deixa o build funcionar em qualquer pasta do servidor (Docker, GitHub Pages...).
export default defineConfig({
  base: './',
  plugins: [react()],
})
