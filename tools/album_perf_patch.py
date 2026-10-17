#!/usr/bin/env python3
"""相册打开卡顿优化。

AlbumUI.refreshView 原本一次性创建 171 个格子（每个还去加载缩略图），
R9s 上会卡约 3 秒。这里改成：
  - 先同步创建前 2 行；
  - 剩余行每帧创建 2 行（setTimeout 0），边显示边加载；
  - content 高度仍一次性设好，滚动条正常。
"""
import sys

NEW_REFRESH = '''t.prototype.refreshView = function() {
var e = this, t = this.albumList.length;
this.content.removeAllChildren(!0);
c.default.LoaderManager.loadAsset("prefabs/album/album_item", function(n) {
var rowCount = Math.ceil(t / 4);
e.content.height = 134 * rowCount + 25;
var row = 0;
var step = function() {
if (!cc.isValid(e.content)) return;
for (var k = 0; k < 2 && row < rowCount; k++, row++) {
var i = new cc.Node();
for (var r = 0; r < 4; r++) if (4 * row + r < t) {
var a = cc.instantiate2(n);
a.setPosition(134 * r - 201.5, 0);
a.getComponent("album_item").refreshItem(e.albumList[4 * row + r]);
i.addChild(a);
}
i.setContentSize(540, 134);
e.content.addChild(i);
}
if (row < rowCount) setTimeout(step, 0);
};
step();
}, cc.Prefab);
};
'''


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/album_perf_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    anchor = text.find("AlbumUI: [")
    if anchor < 0:
        sys.exit("patch refreshView: AlbumUI module not found")
    start = text.find("t.prototype.refreshView = function() {", anchor)
    end = text.find("t.prototype.onClose = function() {", start)
    if start < 0 or end < 0:
        sys.exit("patch refreshView: boundaries not found")
    text = text[:start] + NEW_REFRESH + text[end:]

    open(out, "w", encoding="utf-8").write(text)
    print(f"album patched: {src} -> {out}")


if __name__ == "__main__":
    main()
