/**
 * 轻量全局顶部加载进度条（无第三方依赖）。
 *
 * 用引用计数管理并发请求：第一次 start 显示并缓动增长，最后一次 done 收尾到 100% 后淡出。
 * 由 axios 拦截器驱动（见 utils/request.ts），覆盖所有接口加载的感知反馈。
 */
let active = 0
let progress = 0
let bar: HTMLElement | null = null
let trickleTimer: ReturnType<typeof setInterval> | null = null

function ensureBar(): HTMLElement {
  if (bar) return bar
  const el = document.createElement('div')
  el.setAttribute('aria-hidden', 'true')
  el.style.cssText = [
    'position:fixed',
    'top:0',
    'left:0',
    'height:2px',
    'width:0',
    'z-index:2100',
    'background:var(--ant-primary-color,#1677ff)',
    'box-shadow:0 0 8px rgba(22,119,255,.55)',
    'opacity:0',
    'pointer-events:none',
    'transition:width .2s ease,opacity .3s ease',
  ].join(';')
  document.body.appendChild(el)
  bar = el
  return el
}

function render(p: number): void {
  progress = Math.min(Math.max(p, 0), 0.99)
  const el = ensureBar()
  el.style.opacity = '1'
  el.style.width = `${progress * 100}%`
}

function trickle(): void {
  render(progress + (0.02 + Math.random() * 0.03) * (1 - progress))
}

export function startProgress(): void {
  active += 1
  if (active > 1) return
  render(0.08)
  if (trickleTimer) clearInterval(trickleTimer)
  trickleTimer = setInterval(trickle, 300)
}

export function doneProgress(): void {
  active = Math.max(0, active - 1)
  if (active > 0) return
  if (trickleTimer) {
    clearInterval(trickleTimer)
    trickleTimer = null
  }
  const el = ensureBar()
  el.style.width = '100%'
  setTimeout(() => {
    el.style.opacity = '0'
    setTimeout(() => {
      el.style.width = '0'
      progress = 0
    }, 300)
  }, 150)
}
