import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const siderCollapsed = ref<boolean>(false)
  const activeMenuKey = ref<string>('dashboard')

  function toggleSider() {
    siderCollapsed.value = !siderCollapsed.value
  }

  return { siderCollapsed, activeMenuKey, toggleSider }
})
