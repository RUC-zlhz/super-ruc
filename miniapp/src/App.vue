<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'

onLaunch(() => {
  console.log('SIP miniapp launched')
})
</script>

<style>
page {
  --primary-color: #b70f24;
  --primary-dark: #7f1722;
  --primary-soft: #fff1f2;
  --accent-gold: #d89b2b;
  --accent-blue: #2563eb;
  --accent-green: #16a34a;
  --accent-orange: #ea7a22;
  --secondary-color: #334155;
  --bg-color: #f8f3f4;
  --card-bg: #ffffff;
  --success-color: #15803d;
  --warning-color: #d97706;
  --error-color: #dc2626;
  --border-color: #eee3e6;
  --text-main: #1e293b;
  --text-muted: #667085;
  --shadow-card: 0 12rpx 34rpx rgba(82, 28, 38, 0.08);
  --shadow-soft: 0 8rpx 24rpx rgba(82, 28, 38, 0.06);
  --radius-card: 24rpx;
  --radius-panel: 18rpx;

  --font-base: 14px;
  --font-large: 16px;
  --font-xl: 18px;
  --font-small: 12px;
  --line-height-base: 1.5;

  background-color: var(--bg-color);
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', sans-serif;
  color: var(--text-main);
  font-size: var(--font-base);
  line-height: var(--line-height-base);
  transition: background-color 0.3s ease, color 0.3s ease;
  box-sizing: border-box;
}

view,
text,
input,
textarea,
button {
  box-sizing: border-box;
}

button {
  border-radius: 999rpx;
}

button::after {
  border: none;
}

@media (prefers-color-scheme: dark) {
  page {
    --bg-color: #121018;
    --card-bg: #1f1b24;
    --secondary-color: #cbd5e1;
    --text-main: #f8fafc;
    --text-muted: #a8b0bd;
    --border-color: #3a3038;
    --primary-color: #e2384f;
    --primary-dark: #a61e2d;
    --primary-soft: rgba(226, 56, 79, 0.14);
  }
}

.card {
  background: var(--card-bg);
  border-radius: var(--radius-card);
  padding: 28rpx;
  margin: 16rpx 24rpx;
  box-shadow: var(--shadow-card);
  transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.3s ease;
  border: 1px solid var(--border-color);
}

.card:active {
  transform: scale(0.99);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: #fff;
  border-radius: 999rpx;
  padding: 12px 24px;
  text-align: center;
  font-size: var(--font-large);
  font-weight: 600;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 10rpx 22rpx rgba(183, 15, 36, 0.2);
}

.btn-primary:active {
  background: var(--primary-dark);
  transform: translateY(2px);
  box-shadow: 0 2px 4px rgba(166, 30, 45, 0.2);
}

.title {
  font-size: var(--font-xl);
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 8px;
  transition: color 0.3s ease;
}

.text-muted {
  color: var(--text-muted);
  font-size: var(--font-small);
  transition: color 0.3s ease;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 16rpx;
  border-radius: 999rpx;
  font-size: 12px;
  font-weight: 600;
  transition: background-color 0.3s ease, color 0.3s ease;
}
.status-success { background: #DCFCE7; color: var(--success-color); }
.status-warning { background: #FEF3C7; color: var(--warning-color); }
.status-error { background: #FEE2E2; color: var(--error-color); }
.status-info { background: #E0E7FF; color: #4F46E5; }

@media (prefers-color-scheme: dark) {
  .status-success { background: rgba(21, 128, 61, 0.2); }
  .status-warning { background: rgba(217, 119, 6, 0.2); }
  .status-error { background: rgba(220, 38, 38, 0.2); }
  .status-info { background: rgba(79, 70, 229, 0.2); }

  .btn-primary {
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  }
}
</style>
