/* Service worker do FogoCerto: deixa o site abrir sem internet.
   - Páginas e dado do risco: rede primeiro; se a rede falhar, usa a última cópia salva.
   - Arquivos com hash no nome (JS, CSS, fontes): cache primeiro (nunca mudam).
   Ao mudar a lógica abaixo, troque a VERSAO para limpar os caches antigos. */

const VERSAO = 'fogocerto-v1'
const PRE_CACHE = ['./', 'index.html', 'manifest.webmanifest', 'favicon.svg', 'icon-192.png', 'icon-512.png']

// Cabeçalho que avisa a página de que a resposta veio do cache (sem rede).
const CABECALHO_OFFLINE = 'x-fogocerto-offline'

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(VERSAO)
      .then((cache) => cache.addAll(PRE_CACHE))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((nomes) => Promise.all(nomes.filter((n) => n !== VERSAO).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  )
})

function marcarOffline(resposta) {
  const cabecalhos = new Headers(resposta.headers)
  cabecalhos.set(CABECALHO_OFFLINE, '1')
  return new Response(resposta.body, { status: resposta.status, statusText: resposta.statusText, headers: cabecalhos })
}

async function redePrimeiro(request, chaveCache) {
  const cache = await caches.open(VERSAO)
  try {
    const resposta = await fetch(request)
    if (resposta.ok) cache.put(chaveCache ?? request, resposta.clone())
    return resposta
  } catch (erro) {
    const guardada = await cache.match(chaveCache ?? request)
    if (guardada) return marcarOffline(guardada)
    throw erro
  }
}

async function cachePrimeiro(request) {
  const cache = await caches.open(VERSAO)
  const guardada = await cache.match(request)
  if (guardada) return guardada
  const resposta = await fetch(request)
  if (resposta.ok) cache.put(request, resposta.clone())
  return resposta
}

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return

  if (request.mode === 'navigate') {
    // Qualquer rota (#/panorama etc.) abre o mesmo index.html.
    event.respondWith(redePrimeiro(request, new URL('index.html', self.registration.scope).href))
  } else if (url.pathname.endsWith('/data/risco_atual.json')) {
    // Chave fixa, sem querystring: a última cópia boa sempre serve.
    event.respondWith(redePrimeiro(request, url.origin + url.pathname))
  } else if (url.pathname.includes('/assets/')) {
    event.respondWith(cachePrimeiro(request))
  } else {
    event.respondWith(redePrimeiro(request))
  }
})
