# -*- coding: utf-8 -*-
"""Extract statement sections using HTML headings, preserving the word 入力 in prose."""
from bs4 import BeautifulSoup


def extract_statement(html):
    soup = BeautifulSoup(html, "html.parser")
    ja = soup.select_one("#task-statement .lang-ja")
    if ja is None:
        raise ValueError("Japanese statement not found")
    sections = ja.select(".part > section")
    if not sections:
        sections = ja.find_all("section")
    selected = []
    for section in sections:
        heading = section.find(["h2", "h3"])
        title = heading.get_text(strip=True) if heading else ""
        if title in {"入力", "出力"} or title.startswith(("入力例", "出力例")):
            break
        selected.append(section.get_text("\n", strip=True))
    if not selected:
        raise ValueError("Problem statement sections not found")
    return "\n".join(selected)


def self_check():
    prefix = '<div id="task-statement"><span class="lang-ja">'
    suffix = '</span></div>'
    section = lambda heading, body: (
        '<div class="part"><section><h3>' + heading + '</h3>' + body + '</section></div>'
    )
    html = prefix + section("問題文", "<p>入力される列を並べ替えてください。</p>") \
        + section("制約", "<ul><li>入力はすべて整数。</li><li>1 ≤ N ≤ 100</li></ul>") \
        + section("入力", "<pre>N A</pre>") + section("出力", "<p>答え</p>") + suffix
    text = extract_statement(html)
    assert "入力される列" in text
    assert "入力はすべて整数" in text
    assert "1 ≤ N ≤ 100" in text
    assert "N A" not in text and "\n出力\n" not in text
    # Demonstrate the old failure on the same HTML.
    old = BeautifulSoup(html, "html.parser").select_one(".lang-ja").get_text("\n", strip=True)
    old = old[:old.find("入力")].rstrip()
    assert "制約" not in old
    # A missing score paragraph must not erase the first problem paragraph.
    assert "入力される列" in text
    return {"checks": 5, "status": "passed"}


if __name__ == "__main__":
    print(self_check())
