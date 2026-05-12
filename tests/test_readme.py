from pathlib import Path


def test_readme_removes_discussion_group_and_friend_links():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "## 讨论交流" not in text
    assert "docs/images/discussion-group-qr.jpg" not in text
    assert "## 友情链接" not in text
    assert "[LINUX DO](https://linux.do)" not in text


def test_readme_includes_codex_plus_icon_and_toc():
    text = Path("README.md").read_text(encoding="utf-8")

    assert '<img src="docs/images/codex-plus-plus.png"' in text
    assert 'width="256"' in text
    assert "![Codex++ 后端状态指示灯](docs/images/backend-status-indicator.png)" in text
    assert Path("docs/images/backend-status-indicator.png").exists()
    assert "## 目录" in text
    assert "- [Windows 使用](#windows-使用)" in text
    assert "- [常见问题](#常见问题)" in text


def test_readme_links_to_fork_releases_and_credits_upstream():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "https://github.com/a110q/codexplus/releases/tag/v1.0.5.1" in text
    assert "https://github.com/a110q/codexplus/releases/download/v1.0.5.1/Codex%2B%2B-macOS-arm64.zip" in text
    assert "https://github.com/a110q/codexplus/releases/download/v1.0.5.1/Codex%2B%2B-Windows-x64-portable.zip" in text
    assert "https://github.com/BigPizzaV3/CodexPlusPlus" in text
