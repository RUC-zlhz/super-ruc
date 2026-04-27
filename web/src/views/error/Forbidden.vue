<template>
  <div class="forbidden-wrap">
    <section class="forbidden-card">
      <div class="shield">
        <div class="lock-hole" />
      </div>

      <div class="copy">
        <div class="code">403</div>
        <h1>抱歉，您暂无权限访问该页面</h1>
        <p>您当前的角色或账号权限不足，无法访问此页面或执行此操作。</p>
        <div class="actions">
          <a-button type="primary" size="large" @click="$router.replace('/dashboard')">
            返回首页
          </a-button>
          <a-button type="link" size="large">联系管理员</a-button>
        </div>
      </div>
    </section>

    <footer>© 2026 中国人民大学 · 管理后台</footer>
  </div>
</template>

<style scoped>
.forbidden-wrap {
  position: relative;
  display: grid;
  min-height: calc(100vh - 128px);
  place-items: center;
  overflow: hidden;
}

.forbidden-wrap::before,
.forbidden-wrap::after {
  content: "";
  position: absolute;
  border-radius: 999px;
  border: 1px solid rgba(176, 0, 24, 0.08);
}

.forbidden-wrap::before {
  right: 4vw;
  bottom: 8vh;
  width: 360px;
  height: 360px;
}

.forbidden-wrap::after {
  left: 8vw;
  top: 14vh;
  width: 170px;
  height: 170px;
}

.forbidden-card {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 46px;
  width: min(980px, 92vw);
  padding: 72px 78px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--line-soft);
  border-radius: 28px;
  box-shadow: 0 26px 70px rgba(31, 35, 41, 0.11);
}

.shield {
  position: relative;
  align-self: center;
  justify-self: center;
  width: 240px;
  height: 280px;
  background:
    radial-gradient(circle at 50% 26%, rgba(255, 255, 255, 0.72), transparent 4rem),
    linear-gradient(145deg, #fff1f2, #f7c8cf);
  border: 1px solid rgba(176, 0, 24, 0.12);
  border-radius: 48% 48% 44% 44%;
  clip-path: polygon(50% 0, 90% 16%, 84% 70%, 50% 100%, 16% 70%, 10% 16%);
  box-shadow: 0 26px 40px rgba(176, 0, 24, 0.16);
}

.shield::before {
  content: "";
  position: absolute;
  left: 78px;
  top: 105px;
  width: 84px;
  height: 72px;
  background: linear-gradient(180deg, #e51b33, var(--ruc-red));
  border-radius: 16px;
}

.shield::after {
  content: "";
  position: absolute;
  left: 92px;
  top: 76px;
  width: 56px;
  height: 62px;
  border: 13px solid #d7192d;
  border-bottom: 0;
  border-radius: 28px 28px 0 0;
}

.lock-hole {
  position: absolute;
  left: 114px;
  top: 135px;
  z-index: 1;
  width: 14px;
  height: 14px;
  background: #fff;
  border-radius: 999px;
}

.lock-hole::after {
  content: "";
  position: absolute;
  left: 5px;
  top: 10px;
  width: 4px;
  height: 18px;
  background: #fff;
  border-radius: 999px;
}

.copy {
  align-self: center;
}

.code {
  color: var(--ruc-red);
  font-family: var(--font-number);
  font-size: 108px;
  font-weight: 900;
  line-height: 0.9;
}

h1 {
  margin: 24px 0 14px;
  color: var(--text);
  font-size: 28px;
  font-weight: 800;
}

p {
  margin: 0;
  color: var(--text-2);
  font-size: 16px;
  line-height: 1.8;
}

.actions {
  display: flex;
  align-items: center;
  gap: 22px;
  margin-top: 34px;
}

footer {
  position: absolute;
  bottom: 28px;
  color: var(--text-3);
  font-size: 13px;
}

@media (max-width: 900px) {
  .forbidden-card {
    grid-template-columns: 1fr;
    padding: 42px 28px;
    text-align: center;
  }

  .actions {
    justify-content: center;
  }
}
</style>
