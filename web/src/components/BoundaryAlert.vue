<template>
  <a-alert
    type="warning"
    show-icon
    message="结果为辅助提示，不构成正式结论"
    :description="description"
    class="boundary-alert"
  />
</template>

<script setup lang="ts">
/**
 * C-05：学业/画像分析类页面必须展示此边界提示。
 */
withDefaults(
  defineProps<{ description?: string }>(),
  {
    description:
      '本结果仅为辅助提示，不构成毕业资格、课程替代或教务最终结论；请以学院/学校正式审核结果为准。',
  },
)
</script>

<style scoped>
.boundary-alert {
  margin-bottom: 16px;
}
</style>
