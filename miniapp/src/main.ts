import { createSSRApp } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import App from './App.vue'

const pinia = createPinia()
setActivePinia(pinia)

export function createApp() {
  setActivePinia(pinia)
  const app = createSSRApp(App)
  app.use(pinia)
  return { app }
}
