# Excusas Papitas

Generador web de excusas estilo **PapitasVT** para GitHub Pages.

Lee `public/data/excuses.json`, elige una entrada con **probabilidad weighted-random** y la muestra. Tan simple como eso.

## Demo local

```bash
npm install
npm run dev
```

Abre [http://127.0.0.1:4321](http://127.0.0.1:4321).

## GitHub Pages

Repo: `https://github.com/Drsolus/excusas-papitas`

1. Sube este proyecto al repo.
2. En GitHub → **Settings → Pages → Source: GitHub Actions**.
3. El workflow `.github/workflows/pages.yml` compila y publica en cada push a `main`.
4. URL esperada: `https://drsolus.github.io/excusas-papitas/`

Build local de producción:

```bash
npm run build
npm run preview
```

## Contenido

| Ruta | Qué es |
|------|--------|
| `public/data/excuses.json` | 100 excusas + `probability` |
| `public/img/` | Arte / merch de Papitas |
| `data/solo-papitas/` | Dataset fuente + mensajes reales filtrados |
| `tools/` | CLI opcional del exportador Discord |

## Nota

Proyecto fan, no oficial.
