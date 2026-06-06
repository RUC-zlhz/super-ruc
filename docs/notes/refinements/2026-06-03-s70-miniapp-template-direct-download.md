# 2026-06-03 S70 小程序模板文件直下载与本地落盘

- 关联主计划条目：`S70.1`, `S70.2`, `S70.3`, `S70.4`
- 状态：`[x]` 已完成

## 背景

用户明确要求“小程序里点击模板后，像平时在小程序或公众号里下载文件一样，直接把模板文件下载到手机端”，而不是仅停留在“接口可访问”或“本地 DevTools 可打开”。

现有 `S68.3` 虽然把模板下载改成了“优先 `/file`，失败后回退 `/download` 预签名链接”，但真实手机端仍可能遇到两类问题：

1. `uni.downloadFile` 与普通 `uni.request` 的环境限制不同，真实手机端更容易受到下载域名能力边界影响。
2. 预签名链接会暴露对象存储访问地址；当前生产对象存储运行在容器内 `minio:9000`，并不适合作为手机端直接访问地址。

因此本轮需要把学生端模板下载收口为“由后端认证接口直接返回文件二进制，小程序拿到文件后本地落盘并打开”，以更接近真实手机“文件已下载”的使用体验。

## 目标

1. 学生端模板下载不再依赖对象存储预签名地址作为主路径。
2. 小程序端下载成功后，文件应先保存到本地可访问路径，再尝试打开文档。
3. 若微信基础库支持“保存到系统”，则额外触发系统级保存能力，让用户获得更接近公众号/小程序下载文件的体验。
4. 失败提示尽量显示真实原因，而不是统一笼统报错。

## 实施拆分

- [x] `S70.1` 新增小程序文件下载 helper，使用认证态 `uni.request` 拉取 `/knowledge/templates/{id}/file` 的二进制响应，并解析文件名、后缀和 `content-type`。
- [x] `S70.2` 将模板文件写入小程序本地用户文件目录，不再依赖 `uni.downloadFile` 作为主通道。
- [x] `S70.3` 在微信能力存在时调用 `saveFileToDisk`，让用户可以将下载文件显式保存到系统；随后继续 `openDocument` 打开文件。
- [x] `S70.4` 更新知识库模板下载页面，移除原先“文件流失败后回退预签名 URL”的主逻辑，并将错误提示改为展示真实 message。

## 实现说明

- 新增 `miniapp/src/utils/file.ts`
  - `downloadBinaryFile()`：通过认证态 `uni.request` 获取二进制文件；
  - `saveFileToDiskIfSupported()`：在微信基础库支持时触发系统保存；
  - 统一解析 `Content-Disposition` 和 `Content-Type`，推断最终文件名。
- 更新 `miniapp/src/api/knowledge.ts`
  - `downloadTemplateFile()` 改为走新的二进制 helper；
  - 保留原有 `getTemplateDownloadLink()` / `downloadTemplateFromUrl()` 兼容接口定义，但学生端模板下载页面不再依赖它们作为主路径。
- 更新 `miniapp/src/pages/knowledge/index.vue`
  - 下载按钮将模板名传入下载函数，用于生成更自然的本地文件名；
  - 下载成功后先尝试保存到系统，再打开文档；
  - 错误时显示真实原因；若下载成功但系统保存失败，会显式提示“文件已下载，但保存到系统失败”。

## 验证结果

- `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json`：通过。
- `corepack pnpm -C miniapp build:mp-weixin`：通过，生成物可导入 `miniapp/dist/build/mp-weixin`。

## 结论

本轮完成后，小程序知识库模板下载的主链路已经从“依赖 `downloadFile` + 预签名 URL 回退”收口为“认证接口直取文件二进制 + 本地落盘 + 文档打开 + 可用时保存到系统”。这更符合真实手机用户对“下载模板文件”的预期，也避免把容器内对象存储地址暴露给学生端作为主下载入口。
