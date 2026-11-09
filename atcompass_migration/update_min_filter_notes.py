# -*- coding: utf-8 -*-
from pathlib import Path
file=Path("C:/Users/ejham/theme2026-kaziru/docs/CLUSTER_TAGS.md")
text=file.read_text(encoding="utf-8")
text=text.replace("変更した7ファイルは","変更対象ファイルは")
text=text.replace("変更対象外の既存26ファイルの指摘","変更対象外の既存ファイルの指摘")
text=text.replace("Reactのサーバー描画で101個の円グラフ","Reactのサーバー描画で76個の円グラフ")
file.write_text(text,encoding="utf-8")
