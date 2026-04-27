const TAB_BAR_PAGES = new Set([
  "/pages/index/index",
  "/pages/notice/index",
  "/pages/profile/index",
]);

export function openMiniappPage(url: string) {
  const [path] = url.split("?");
  return new Promise<any>((resolve, reject) => {
    if (TAB_BAR_PAGES.has(path)) {
      uni.switchTab({
        url: path,
        success: resolve,
        fail: reject,
      });
      return;
    }
    uni.navigateTo({
      url,
      success: resolve,
      fail: reject,
    });
  });
}

export function openNoticeDetail(noticeId: number, deliveryId?: number | null) {
  const query = [`noticeId=${noticeId}`];
  if (deliveryId != null) {
    query.push(`deliveryId=${deliveryId}`);
  }
  return openMiniappPage(`/pages/notice/detail?${query.join("&")}`);
}
