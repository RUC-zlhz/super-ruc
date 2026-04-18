<template>
  <div class="forbidden-wrap">
    <a-result
      status="403"
      title="403"
      sub-title="抱歉，您没有权限访问该页面。"
    >
      <template #extra>
        <a-button type="primary" @click="$router.replace('/dashboard')">
          返回首页
        </a-button>
      </template>
    </a-result>
  </div>
</template>

<style scoped>
.forbidden-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}
</style>
