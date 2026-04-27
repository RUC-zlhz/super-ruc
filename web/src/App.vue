<template>
  <a-config-provider :locale="zhCN" :theme="themeConfig">
    <router-view v-slot="{ Component }">
      <transition name="fade-slide" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'

const themeConfig = computed(() => {
  return {
    token: {
      colorPrimary: '#b00018',
      colorInfo: '#b00018',
      colorSuccess: '#25a66a',
      colorWarning: '#d8941f',
      colorError: '#c40018',
      colorTextBase: '#1f2329',
      colorBgBase: '#ffffff',
      colorBgLayout: '#f5f6f8',
      colorBorder: '#e6e8ee',
      colorBorderSecondary: '#eff1f5',
      borderRadius: 8,
      borderRadiusLG: 12,
      borderRadiusSM: 6,
      fontFamily:
        "'Alibaba PuHuiTi', 'HarmonyOS Sans SC', 'Microsoft YaHei UI', 'Microsoft YaHei', sans-serif",
      fontSize: 13,
      controlHeight: 34,
    },
  }
})
</script>

<style>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(15px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-15px);
}
</style>
