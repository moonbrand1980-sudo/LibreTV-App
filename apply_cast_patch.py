#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LibreTV / LibreTV-App 自动注入安卓后台投屏功能脚本
运行方式：在项目根目录下执行 `python3 apply_cast_patch.py`
"""
import os
import re
import glob

CAST_INJECT_JS = """
// ================= [LibreTV Android 后台投屏扩展] =================
(function() {
    function extractRealM3u8Url(rawUrl) {
        if (!rawUrl) return '';
        try {
            const u = new URL(rawUrl, window.location.origin);
            const target = u.searchParams.get('url');
            if (target && target.startsWith('http')) {
                return decodeURIComponent(target);
            }
        } catch (e) {}
        return rawUrl;
    }

    window.__libretvTriggerCast = function(artInstance, fallbackUrl) {
        const currentUrl = (artInstance && artInstance.url) ? artInstance.url : fallbackUrl;
        const realUrl = extractRealM3u8Url(currentUrl);
        if (!realUrl) {
            alert('未检测到有效的视频播放地址，请等待视频加载后再点投屏');
            return;
        }

        // 1. 立即暂停手机端播放，释放手机音频焦点与解码器，不影响手机切后台聊微信/锁屏
        try {
            if (artInstance && typeof artInstance.pause === 'function') {
                artInstance.pause();
            }
            document.querySelectorAll('video').forEach(v => v.pause());
        } catch (e) {}

        // 2. 自动复制真实直链到剪贴板作为保底
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(realUrl).catch(() => {});
        }

        // 3. 优先调用 Android 原生 JavascriptInterface 桥接（不被 WebView 拦截）
        if (window.AndroidCast && typeof window.AndroidCast.castVideo === 'function') {
            window.AndroidCast.castVideo(realUrl, document.title || 'LibreTV 视频');
            return;
        }

        // 4. 备用：通过标准 Android Intent URI 唤起外部投屏器（Web Video Caster / VLC 等）
        const cleanUrl = realUrl.replace(/^https?:\/\//, '');
        const scheme = realUrl.startsWith('https') ? 'https' : 'http';
        const intentUrl = `intent://${cleanUrl}#Intent;scheme=${scheme};type=video/*;action=android.intent.action.VIEW;end`;
        window.location.href = intentUrl;
    };

    // 在页面右下角或播放器控制栏动态挂载悬浮/内嵌投屏按钮（兼容所有 LibreTV 分支版本）
    function mountFloatingCastBtn() {
        if (document.getElementById('libretv-cast-fab')) return;
        const btn = document.createElement('button');
        btn.id = 'libretv-cast-fab';
        btn.innerHTML = '📺 投屏电视';
        btn.style.cssText = 'position:fixed;bottom:24px;right:20px;z-index:99999;background:linear-gradient(135deg,#0ea5e9,#2563eb);color:#fff;border:none;border-radius:999px;padding:10px 18px;font-size:14px;font-weight:bold;box-shadow:0 4px 14px rgba(37,99,235,0.45);cursor:pointer;display:none;align-items:center;gap:6px;';
        btn.onclick = function() {
            const art = window.art || window.player || null;
            let videoUrl = art ? art.url : '';
            if (!videoUrl) {
                const v = document.querySelector('video');
                if (v && v.src && !v.src.startsWith('blob:')) videoUrl = v.src;
            }
            window.__libretvTriggerCast(art, videoUrl);
        };
        document.body.appendChild(btn);

        // 当页面存在 video 标签或处于播放页时显示投屏按钮
        setInterval(() => {
            const hasVideo = !!document.querySelector('video') || window.location.pathname.includes('player') || window.location.pathname.includes('watch');
            btn.style.display = hasVideo ? 'flex' : 'none';
        }, 1000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mountFloatingCastBtn);
    } else {
        mountFloatingCastBtn();
    }
})();
// =================================================================
"""

ARTPLAYER_CONTROL_SNIPPET = """
            {
                position: 'right',
                html: '<span style="font-size:14px;cursor:pointer;font-weight:bold;color:#38bdf8;padding:0 6px;">📺 投屏</span>',
                tooltip: '投屏到电视（手机可切后台）',
                click: function () {
                    if (window.__libretvTriggerCast) {
                        window.__libretvTriggerCast(this, this.url);
                    }
                },
            },
"""

def patch_frontend_files():
    patched_any = False
    # 查找可能的播放器 JS 文件
    candidates = glob.glob('js/**/*.js', recursive=True) + glob.glob('src/**/*.tsx', recursive=True) + glob.glob('src/**/*.ts', recursive=True)
    for filepath in candidates:
        if not os.path.isfile(filepath):
            continue
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if 'new Artplayer' in content and '__libretvTriggerCast' not in content:
            print(f'[+] 发现 ArtPlayer 初始化文件: {filepath}')
            # 注入全局辅助函数到文件末尾
            new_content = content + '\n' + CAST_INJECT_JS
            # 如果存在 controls: [，自动插入投屏按钮
            if 'controls:' in new_content:
                new_content = re.sub(
                    r'(controls\s*:\s*\[)',
                    r'\1\n' + ARTPLAYER_CONTROL_SNIPPET,
                    new_content,
                    count=1
                )
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            patched_any = True

    # 同时检查 player.html / watch.html 保底注入
    for html_file in ['player.html', 'watch.html', 'index.html']:
        if os.path.isfile(html_file):
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                h_content = f.read()
            if '__libretvTriggerCast' not in h_content and '</body>' in h_content:
                print(f'[+] 注入投屏脚本到页面: {html_file}')
                h_content = h_content.replace('</body>', f'<script>{CAST_INJECT_JS}</script>\n</body>')
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(h_content)
                patched_any = True

    return patched_any

def patch_android_kotlin():
    # 查找 MainActivity.kt
    kt_files = glob.glob('src-tauri/gen/android/**/MainActivity.kt', recursive=True)
    for kt_path in kt_files:
        with open(kt_path, 'r', encoding='utf-8', errors='ignore') as f:
            kt_content = f.read()

        if 'AndroidCast' in kt_content:
            print(f'[i] {kt_path} 已包含 AndroidCast 桥接，跳过')
            continue

        # 提取真实 package 名称
        pkg_match = re.search(r'^package\s+([a-zA-Z0-9_.]+)', kt_content, re.MULTILINE)
        pkg_name = pkg_match.group(1) if pkg_match else 'com.libretv.app'

        new_kt = f"""package {pkg_name}

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.Toast

class MainActivity : TauriActivity() {{

    override fun onWebViewCreate(webView: WebView) {{
        super.onWebViewCreate(webView)
        webView.settings.mediaPlaybackRequiresUserGesture = false
        webView.addJavascriptInterface(CastBridge(), "AndroidCast")
    }}

    inner class CastBridge {{
        @JavascriptInterface
        fun castVideo(videoUrl: String, title: String?) {{
            runOnUiThread {{
                try {{
                    val intent = Intent(Intent.ACTION_VIEW).apply {{
                        setDataAndType(Uri.parse(videoUrl), "video/*")
                        if (!title.isNullOrEmpty()) {{
                            putExtra("title", title)
                            putExtra(Intent.EXTRA_TITLE, title)
                        }}
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    }}
                    val chooser = Intent.createChooser(intent, "选择投屏器或播放器（手机可切后台）")
                    startActivity(chooser)
                }} catch (e: Exception) {{
                    Toast.makeText(
                        this@MainActivity,
                        "未找到外部投屏软件！视频直链已自动复制，请安装 Web Video Caster 或 VLC",
                        Toast.LENGTH_LONG
                    ).show()
                }}
            }}
        }}
    }}
}}
"""
        with open(kt_path, 'w', encoding='utf-8') as f:
            f.write(new_kt)
        print(f'[+] 已更新 Android 原生投屏桥接: {kt_path}')

    # 开启 AndroidManifest.xml 明文 HTTP 支持
    manifest_files = glob.glob('src-tauri/gen/android/**/AndroidManifest.xml', recursive=True)
    for mf_path in manifest_files:
        with open(mf_path, 'r', encoding='utf-8', errors='ignore') as f:
            mf_content = f.read()
        if 'usesCleartextTraffic' not in mf_content and '<application' in mf_content:
            mf_content = mf_content.replace('<application', '<application android:usesCleartextTraffic="true"', 1)
            with open(mf_path, 'w', encoding='utf-8') as f:
                f.write(mf_content)
            print(f'[+] 已开启 Android 明文流量支持: {mf_path}')

if __name__ == '__main__':
    print('=== 开始执行 LibreTV 安卓后台投屏补丁 ===')
    patch_frontend_files()
    patch_android_kotlin()
    print('=== 补丁注入完成 ===')
