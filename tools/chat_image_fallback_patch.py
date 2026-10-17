#!/usr/bin/env python3
"""聊天图片预览离线兜底：远程 chatImg_big 加载失败时改用包内缩略图。"""
import sys

NEW = '''t.prototype.show = function(e, t) {
this.callBack = t;
this.img.node.scale = 0;
this.url = e;
var n = this;
this._imageLoaded = false;
setTimeout(function() {
if (!n._imageLoaded && n.node && n.node.isValid) failSafe();
}, 1500);
function toFrame(asset) {
if (!asset) return null;
if (asset.getRect && asset.getTexture) return asset;
if (asset.spriteFrame) return asset.spriteFrame;
if (asset.width !== undefined && asset.height !== undefined) {
try { return new cc.SpriteFrame(asset); } catch (e) { return null; }
}
return null;
}
function applyFrame(sf) {
if (!sf || !n.node || !n.node.isValid) return;
n._imageLoaded = true;
n.img.spriteFrame = sf;
var w = 540, h = 540;
try {
var tex = sf.getTexture && sf.getTexture();
if (tex && tex.width > 0 && tex.height > 0) { w = tex.width; h = tex.height; }
else {
var size = sf.getOriginalSize();
if (size && size.width > 0 && size.height > 0) { w = size.width; h = size.height; }
}
} catch (e) { w = 540; h = 540; }
if (!isFinite(w) || !isFinite(h) || w <= 0 || h <= 0) { w = 540; h = 540; }
n.img.node.setContentSize(540, 540 / w * h);
n.btn.width = Math.max(n.img.node.getContentSize().width, 540);
n.btn.height = Math.max(n.img.node.getContentSize().height, 960);
}
function fallbackLocal() {
var m = String(e).match(/chatImg_([0-9]+)\\.png/);
if (!m) return;
cc.loader.loadRes("sprites/chatImg/chatImg_" + m[1], null, function(err, asset) {
var sf = toFrame(asset);
if (sf) applyFrame(sf);
else failSafe();
});
}
function failSafe() {
n._imageLoaded = true;
r.default.showToast("图片加载失败");
if (n.node && n.node.isValid) n.node.destroy();
}
var direct = window.__dajuChatImageFrame;
window.__dajuChatImageFrame = null;
if (direct) {
applyFrame(direct);
r.default.showNode(this.img.node);
return;
}
var match = String(e).match(/chatImg_([0-9]+)\.png/);
if (match) {
cc.loader.loadRes("sprites/chatImg/chatImg_" + match[1], null, function(err, asset) {
var sf = toFrame(asset);
if (sf) applyFrame(sf);
else failSafe();
});
} else {
cc.loader.load(e, function(err, tex) {
if (tex) applyFrame(new cc.SpriteFrame(tex));
else fallbackLocal();
});
}
r.default.showNode(this.img.node);
};
'''


def patch_caller(text: str) -> str:
    marker = "t.prototype.onClickImageContentAction = function() {"
    start = text.find(marker)
    if start < 0:
        sys.exit("onClickImageContentAction not found")
    end = text.find("t.prototype.canClick = function()", start)
    if end < 0:
        end = text.find("t.prototype.onClickImageContentAction", start + len(marker))
    chunk = text[start:end]
    chunk = chunk.replace(
        "f.default.showBigImage(t);",
        "window.__dajuChatImageFrame = i.chatImage && i.chatImage.spriteFrame;\nf.default.showBigImage(t);"
    )
    return text[:start] + chunk + text[end:]

def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/chat_image_fallback_patch.py <in.js> <out.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()
    module = text.find("ImageView: [")
    start = text.find("t.prototype.show = function(e, t) {", module)
    end = text.find("t.prototype.doubleClick = function() {", start)
    if module < 0 or start < 0 or end < 0:
        sys.exit("ImageView.show boundaries not found")
    text = text[:start] + NEW + text[end:]
    text = patch_caller(text)
    open(out, "w", encoding="utf-8").write(text)
    print(f"chat image fallback patched: {src} -> {out}")


if __name__ == "__main__":
    main()
