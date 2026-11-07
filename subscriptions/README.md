# 订阅源（LibreTV）

放这里是为了给订阅地址一个**不会过期**的托管位置。以前用的 dpaste 免费 paste 30 天就删除，
链接直接 404，换手机或重装就再也导不回来。

## 文件

| 文件 | 用途 |
| --- | --- |
| `libretv-sources.json` | 订阅主文件：8 个点播源 + 2 个直播列表入口，App 直接导入这个 |
| `libretv-live.m3u` | 精选中文直播 22 台（逐台 Range 探测，只留 200/206 的） |

## 订阅地址

```
https://cdn.jsdelivr.net/gh/moonbrand1980-sudo/LibreTV-App@main/subscriptions/libretv-sources.json
```

备用（jsDelivr 抽风时用）：

```
https://raw.githubusercontent.com/moonbrand1980-sudo/LibreTV-App/main/subscriptions/libretv-sources.json
```

## 更新

改完 JSON 提交到 `main` 即可。jsDelivr 默认缓存 12 小时，想立刻生效就在地址后面加
`?v=20261107` 这类版本串；raw.githubusercontent 基本是即时的。

## 说明

- 8 个点播源与 App 内置的 `API_SITES` **完全一致**，所以 App 里导入这份订阅不会有新增源，
  它主要是给换设备 / 其它播放器用的备份入口。
- 直播列表 App 目前不解析（未移植直播模块），只供支持 m3u 的播放器使用。
- 核实时间 2026-11-07：点播 8/8 可用；直播 22 台全部 200/206（已剔除 CCTV-15 音乐、
  东方卫视国际、广州电视台 3 条死链并补入替代）。
