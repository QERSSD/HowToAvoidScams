# -*- coding: utf-8 -*-
"""入库后一键同步重建站点产物。

构建链（与 build_repo.py 注释一致）：
    1. build_offline.py  -> index.html / 人间防骗指南.html（离线单文件应用）
    2. build_repo.py     -> book/ 16 卷 + docs/ + README.md（并复制 index.html）

用法：
    python tools/rebuild_site.py
也可被各 add_articles_*.py 在入库成功后自动调用，保证 articles.json
一旦变动，book / 站点 HTML / README 同步刷新，不再漏更。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("build_offline.py", "站点 HTML（index.html / 人间防骗指南.html）"),
    ("build_repo.py", "book/ 分卷 + docs/ + README.md"),
]


def rebuild():
    for script, what in STEPS:
        path = os.path.join(HERE, script)
        print(">> 重建 %s …（%s）" % (script, what))
        rc = subprocess.run([sys.executable, path], check=False).returncode
        if rc != 0:
            print("   ⚠️ %s 退出码 %d，请检查" % (script, rc))
        else:
            print("   ✅ 完成")


if __name__ == "__main__":
    rebuild()
