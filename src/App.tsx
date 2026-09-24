import { useEffect, useState, useTransition } from 'react'
import {
  categoryLabel,
  formatProbability,
  pickExcuse,
  type Excuse,
  type ExcuseDataset,
} from './lib/excuses'

const IMG = {
  plush: `${import.meta.env.BASE_URL}img/plush.png`,
  wink: `${import.meta.env.BASE_URL}img/wink.png`,
  headphones: `${import.meta.env.BASE_URL}img/headphones.png`,
  gigachad: `${import.meta.env.BASE_URL}img/gigachad.png`,
} as const

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: ExcuseDataset }

export default function App() {
  const [load, setLoad] = useState<LoadState>({ status: 'loading' })
  const [current, setCurrent] = useState<Excuse | null>(null)
  const [spinKey, setSpinKey] = useState(0)
  const [isPending, startTransition] = useTransition()

  useEffect(() => {
    let cancelled = false

    async function loadData() {
      try {
        const response = await fetch(`${import.meta.env.BASE_URL}data/excuses.json`)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const data = (await response.json()) as ExcuseDataset
        if (!cancelled) setLoad({ status: 'ready', data })
      } catch (error) {
        if (!cancelled) {
          setLoad({
            status: 'error',
            message:
              error instanceof Error
                ? error.message
                : 'No se pudo cargar excuses.json',
          })
        }
      }
    }

    void loadData()
    return () => {
      cancelled = true
    }
  }, [])

  function generate() {
    if (load.status !== 'ready') return
    startTransition(() => {
      const next = pickExcuse(load.data.excuses)
      setCurrent(next)
      setSpinKey((value) => value + 1)
    })
  }

  return (
    <div className="relative min-h-dvh bg-ink text-snow">
      <div className="scanline" aria-hidden />
      <div
        className="pointer-events-none fixed inset-0 opacity-80"
        style={{
          background:
            'radial-gradient(ellipse 70% 50% at 15% 20%, rgb(255 45 85 / 0.22), transparent 55%), radial-gradient(ellipse 60% 45% at 85% 15%, rgb(46 230 214 / 0.16), transparent 50%), radial-gradient(ellipse 50% 40% at 70% 90%, rgb(255 209 26 / 0.1), transparent 55%)',
        }}
        aria-hidden
      />
      <div className="grid-glow pointer-events-none fixed inset-0" aria-hidden />

      <div
        className="pointer-events-none absolute left-0 top-[12%] hidden w-[min(38vw,340px)] anim-float-a md:block"
        aria-hidden
      >
        <img
          src={IMG.headphones}
          alt=""
          className="w-full drop-shadow-[0_20px_50px_rgb(46_230_214_/0.25)]"
        />
      </div>
      <div
        className="pointer-events-none absolute right-[-2%] top-[8%] hidden w-[min(34vw,300px)] anim-float-b lg:block"
        aria-hidden
      >
        <img
          src={IMG.wink}
          alt=""
          className="w-full drop-shadow-[0_18px_40px_rgb(255_45_85_/0.28)]"
        />
      </div>
      <div
        className="pointer-events-none absolute bottom-[4%] left-[4%] hidden w-[min(28vw,220px)] anim-float-b md:block"
        aria-hidden
      >
        <img
          src={IMG.plush}
          alt=""
          className="w-full drop-shadow-[0_16px_36px_rgb(255_209_26_/0.22)]"
        />
      </div>
      <div
        className="pointer-events-none absolute bottom-[6%] right-[3%] hidden w-[min(24vw,180px)] opacity-90 anim-float-a xl:block"
        aria-hidden
      >
        <img
          src={IMG.gigachad}
          alt=""
          className="w-full rounded-sm shadow-[0_0_0_1px_rgb(255_209_26_/0.35)]"
        />
      </div>

      <main className="relative z-20 mx-auto flex min-h-dvh w-full max-w-3xl flex-col justify-center px-5 py-16 sm:px-8">
        <header className="mb-10 text-center md:mb-12">
          <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.35em] text-signal">
            solo-papitas // excuse.runtime
          </p>
          <h1 className="font-display text-[clamp(2.6rem,10vw,5.2rem)] font-extrabold leading-[0.92] tracking-tight">
            <span className="bg-gradient-to-br from-fry via-snow to-signal bg-clip-text text-transparent">
              EXCUSAS
            </span>
            <br />
            <span className="text-sauce">PAPITAS</span>
          </h1>
          <p className="mx-auto mt-5 max-w-md font-body text-base leading-relaxed text-mist sm:text-lg">
            Generador de excusas!  suelta
            un descansito digno de VAGA.
          </p>
        </header>

        <div className="mb-8 flex items-center justify-center gap-3 md:hidden">
          <img src={IMG.plush} alt="Peluche Papitas" className="h-20 w-auto" />
          <img src={IMG.wink} alt="Papitas guiñando" className="h-20 w-auto" />
        </div>

        <div className="flex flex-col items-center gap-6">
          <div className="relative">
            {(isPending || spinKey > 0) && (
              <span
                className="anim-pulse-ring pointer-events-none absolute inset-[-10px] rounded-full border border-signal/50"
                aria-hidden
              />
            )}
            <button
              type="button"
              onClick={generate}
              disabled={load.status !== 'ready'}
              className="group relative z-10 cursor-pointer overflow-hidden rounded-full bg-sauce px-10 py-4 font-display text-lg font-bold tracking-wide text-snow shadow-[0_0_0_1px_rgb(255_209_26_/0.45),0_12px_40px_rgb(255_45_85_/0.35)] transition enabled:hover:-translate-y-0.5 enabled:hover:bg-[#ff4066] enabled:active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="relative z-10">
                {load.status === 'loading'
                  ? 'Cargando dataset…'
                  : isPending
                    ? 'Tirando RNG…'
                    : current
                      ? 'Otra excusa'
                      : 'Generar excusa'}
              </span>
              <span
                className="pointer-events-none absolute inset-0 translate-x-[-120%] bg-gradient-to-r from-transparent via-fry/30 to-transparent transition duration-700 group-hover:translate-x-[120%]"
                aria-hidden
              />
            </button>
          </div>

          {load.status === 'ready' && (
            <p className="font-mono text-xs text-mist/80">
              pool={load.data.meta.count} · Σp=
              {load.data.meta.probability_sum}
            </p>
          )}

          {load.status === 'error' && (
            <p className="rounded-md border border-sauce/40 bg-panel px-4 py-3 text-sm text-sauce">
              Error cargando excusas: {load.message}
            </p>
          )}
        </div>

        <section className="mt-10 min-h-[220px]" aria-live="polite">
          {current ? (
            <article
              key={spinKey}
              className="anim-reveal relative overflow-hidden rounded-2xl border border-signal/20 bg-panel/80 p-6 shadow-[0_0_80px_rgb(46_230_214_/0.08)] backdrop-blur-md sm:p-8"
            >
              <div
                className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-sauce/20 blur-2xl"
                aria-hidden
              />
              <div className="mb-4 flex flex-wrap items-center gap-2 font-mono text-[11px] uppercase tracking-wider">
                <span className="rounded-full border border-fry/40 bg-fry/10 px-3 py-1 text-fry">
                  {categoryLabel(current.category)}
                </span>
                <span className="rounded-full border border-signal/30 bg-signal/10 px-3 py-1 text-signal">
                  p={formatProbability(current.probability)}
                </span>
                <span className="rounded-full border border-mist/20 px-3 py-1 text-mist">
                  {current.id}
                </span>
              </div>
              <p className="font-body text-lg leading-relaxed text-snow sm:text-xl whitespace-pre-wrap">
                {current.text}
              </p>
            </article>
          ) : (
            <div className="rounded-2xl border border-dashed border-mist/20 bg-panel/40 px-6 py-10 text-center text-mist">
              <p className="font-body text-base">
                Presiona el botón y que el RNG decida si hoy toca sueño, chamba
                invisible… o Citrus (improbable).
              </p>
            </div>
          )}
        </section>

        <footer className="mt-14 text-center font-mono text-[10px] uppercase tracking-[0.28em] text-mist/60">
          fan project · no oficial · papitas energy
        </footer>
      </main>
    </div>
  )
}
