import type { SVGProps } from 'react'

type P = SVGProps<SVGSVGElement>

const base = (p: P): P => ({
  width: 24,
  height: 24,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
  focusable: false,
  ...p,
})

export const IconeChama = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 2.5c1 3.5 5.5 5.6 5.5 11a5.5 5.5 0 0 1-11 0c0-2.8 1.5-4.4 2.7-5.5 0 2.3 1.1 3.4 2.3 3.4-.8-3.1.5-6.2.5-8.9z" />
  </svg>
)
export const IconeGota = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 3s6 6.4 6 11a6 6 0 0 1-12 0c0-4.6 6-11 6-11z" />
  </svg>
)
export const IconeVento = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 8h11a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h8" />
  </svg>
)
export const IconeChuva = (p: P) => (
  <svg {...base(p)}>
    <path d="M7 15a4 4 0 0 1-.6-8 5.5 5.5 0 0 1 10.6 1.5A3.3 3.3 0 0 1 17 15H7z" />
    <path d="M8 18l-1 3M12 18l-1 3M16 18l-1 3" />
  </svg>
)
export const IconeTermometro = (p: P) => (
  <svg {...base(p)}>
    <path d="M10 13.5V5a2 2 0 1 1 4 0v8.5a4 4 0 1 1-4 0z" />
    <path d="M12 9v7" />
  </svg>
)
export const IconeRelogio = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </svg>
)
export const IconeAlerta = (p: P) => (
  <svg {...base(p)}>
    <path d="M10.3 3.9 2.4 17.5A2 2 0 0 0 4.1 20.5h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
    <path d="M12 9v4M12 17h.01" />
  </svg>
)
export const IconeLei = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 3v18M5 21h14M4 7h16M7 7l-3 7a3 3 0 0 0 6 0L7 7zM17 7l-3 7a3 3 0 0 0 6 0l-3-7z" />
  </svg>
)
export const IconeTelefone = (p: P) => (
  <svg {...base(p)}>
    <path d="M5 3h3l2 5-2.5 1.5a11 11 0 0 0 7 7L16 14l5 2v3a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2z" />
  </svg>
)
export const IconeInicio = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 11 12 4l9 7M5 10v10h5v-6h4v6h5V10" />
  </svg>
)
export const IconeLista = (p: P) => (
  <svg {...base(p)}>
    <path d="M4 6h3M4 12h3M4 18h3M10 6h10M10 12h7M10 18h4" />
  </svg>
)
export const IconeRegua = (p: P) => (
  <svg {...base(p)}>
    <path d="M4 20 20 4M7 17l-2-2M10 14l-1.5-1.5M13 11l-2-2M16 8l-1.5-1.5" />
  </svg>
)
export const IconeBalao = (p: P) => (
  <svg {...base(p)}>
    <path d="M4 5h16v11H9l-5 4V5z" />
    <path d="M8 9h8M8 12h5" />
  </svg>
)
export const IconeCamera = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 8h4l2-3h6l2 3h4v11H3V8z" />
    <circle cx="12" cy="13" r="3.5" />
  </svg>
)
export const IconeSeta = (p: P) => (
  <svg {...base(p)}>
    <path d="M9 6l6 6-6 6" />
  </svg>
)
export const IconeRecarregar = (p: P) => (
  <svg {...base(p)}>
    <path d="M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5" />
  </svg>
)
