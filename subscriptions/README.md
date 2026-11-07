# 订阅源（LibreTV）

放这里是为了给订阅地址一个**不会过期**的托管位置。以前用的 dpaste 免费 paste 30 天就删除，
链接直接 404，换手机或重装就再也导不回来。

## 文件

| 文件 | 用途 |
| --- | --- |
| `libretv-sources.json` | 订阅主文件：5 个新增点播源 + 2 个直播列表入口，App 直接导入这个 |
| `libretv-live.m3u` | 精选中文直播 22 台（逐台 Range 探测，只留 200/206 的） |

## 订阅地址

```
https://cdn.jsdelivr.net/gh/moonbrand1980-sudo/LibreTV-App@main/subscriptions/libretv-sources.json
```

备用（jsDelivr 抽风时用，国内可直连）：

```
https://gh-proxy.com/https://raw.githubusercontent.com/moonbrand1980-sudo/LibreTV-App/main/subscriptions/libretv-sources.json
```

`raw.githubusercontent.com` 直链在部分网络下不可达（需要代理），所以没把它写进备用位。

## 更新

改完 JSON 提交到 `main` 即可。jsDelivr 对分支引用有缓存，提交后可能仍返回旧内容；
清一下缓存再访问就能立刻读到新版：

```
https://purge.jsdelivr.net/gh/moonbrand1980-sudo/LibreTV-App@main/subscriptions/libretv-sources.json
```

## 说明

- 订阅里只放 **App 内置 `API_SITES` 之外**的源，导入不会和内置的 8 个重复。
- 当前 5 个新增源（2026-11-07 各测两轮，搜索 → m3u8 → 首个分片全部 206）：

  | 源 | 响应 | 说明 |
  | --- | --- | --- |
  | 量子资源 | 2.2s | 片库最大，20 条命中，首选 |
  | 红牛资源 | 3.3s | 更新快 |
  | 光速资源 | 4.6s | 体育赛事较多 |
  | 无尽资源 | 5.7s | — |
  | 豪华资源 | 4.3–7.9s | 最慢，兜底用 |

- 直播列表 App 目前不解析（未移植直播模块），只供支持 m3u 的播放器使用。
- 核实时间 2026-11-07：直播 22 台全部 200/206（已剔除 CCTV-15 音乐、东方卫视国际、
  广州电视台 3 条死链并补入替代）。
