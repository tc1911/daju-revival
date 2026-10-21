package org.cocos2dx.javascript;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.graphics.drawable.GradientDrawable;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.preference.PreferenceManager;
import android.text.InputType;
import android.util.Log;
import android.widget.Toast;
import android.widget.EditText;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.Method;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

public class ProfileBridge implements PreferenceManager.OnActivityResultListener {
    private static ProfileBridge instance;
    private static final int REQ_AVATAR = 1001;
    private static final int REQ_EXPORT = 1002;
    private static final int REQ_IMPORT = 1003;
    private static String pendingExportJson;

    private static Activity activity() {
        try {
            Class<?> c = Class.forName("org.cocos2dx.lib.Cocos2dxHelper");
            Method m = c.getMethod("getActivity");
            return (Activity) m.invoke(null);
        } catch (Throwable t) {
            return null;
        }
    }

    private static void eval(final String js) {
        try {
            Class<?> c = Class.forName("org.cocos2dx.lib.Cocos2dxHelper");
            Method m = c.getMethod("runOnGLThread", Runnable.class);
            m.invoke(null, new Runnable() {
                public void run() {
                    try {
                        Class<?> b = Class.forName("org.cocos2dx.lib.Cocos2dxJavascriptJavaBridge");
                        Method e = b.getMethod("evalString", String.class);
                        e.invoke(null, js);
                        Log.e("ProfileBridge", "eval ok: " + js);
                    } catch (Throwable ignored) {
                    }
                }
            });
        } catch (Throwable ignored) {
        }
    }

    private static String esc(String s) {
        return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "");
    }

    private static int dp(Activity a, int v) {
        return (int) (v * a.getResources().getDisplayMetrics().density + 0.5f);
    }

    public static void showNickname(final String current) {
        final Activity a = activity();
        if (a == null) return;
        a.runOnUiThread(new Runnable() {
            public void run() {
                final LinearLayout root = new LinearLayout(a);
                root.setOrientation(LinearLayout.VERTICAL);
                root.setPadding(dp(a, 22), dp(a, 18), dp(a, 22), dp(a, 12));
                GradientDrawable bg = new GradientDrawable();
                bg.setColor(0xFFF8F4EC);
                bg.setCornerRadius(dp(a, 18));
                root.setBackground(bg);

                TextView title = new TextView(a);
                title.setText("修改昵称");
                title.setTextColor(0xFF5A4632);
                title.setTextSize(20);
                title.setPadding(0, 0, 0, dp(a, 12));
                root.addView(title);

                final EditText et = new EditText(a);
                et.setText(current == null ? "" : current);
                et.setSelection(et.getText().length());
                et.setSingleLine(true);
                et.setTextSize(16);
                et.setTextColor(0xFF3A2E22);
                et.setHint("输入昵称");
                et.setPadding(dp(a, 12), dp(a, 8), dp(a, 12), dp(a, 8));
                GradientDrawable etBg = new GradientDrawable();
                etBg.setColor(0xFFFFFFFF);
                etBg.setCornerRadius(dp(a, 10));
                etBg.setStroke(1, 0xFFD8CCBC);
                et.setBackground(etBg);
                root.addView(et);

                LinearLayout buttons = new LinearLayout(a);
                buttons.setOrientation(LinearLayout.HORIZONTAL);
                buttons.setGravity(android.view.Gravity.END);
                TextView cancel = new TextView(a);
                cancel.setText("取消");
                cancel.setTextColor(0xFF7A6854);
                cancel.setTextSize(16);
                cancel.setPadding(dp(a, 18), dp(a, 10), dp(a, 18), dp(a, 10));
                buttons.addView(cancel);
                TextView save = new TextView(a);
                save.setText("保存");
                save.setTextColor(0xFFB0612A);
                save.setTextSize(16);
                save.setPadding(dp(a, 18), dp(a, 10), dp(a, 18), dp(a, 10));
                buttons.addView(save);
                root.addView(buttons);

                final AlertDialog dialog = new AlertDialog.Builder(a).setView(root).create();
                dialog.show();
                android.view.Window win = dialog.getWindow();
                if (win != null) {
                    win.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(0x00000000));
                    win.setLayout(dp(a, 320), android.view.ViewGroup.LayoutParams.WRAP_CONTENT);
                    win.setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
                }
                et.requestFocus();
                cancel.setOnClickListener(new View.OnClickListener() {
                    public void onClick(View v) { dialog.dismiss(); }
                });
                save.setOnClickListener(new View.OnClickListener() {
                    public void onClick(View v) {
                        String name = et.getText().toString().trim();
                        dialog.dismiss();
                        if (name.length() == 0) return;
                        eval("window.onNativeNickname && window.onNativeNickname('" + esc(name) + "')");
                    }
                });
            }
        });
    }

    public static void exportSave(final String json) {
        final Activity a = activity();
        if (a == null) return;
        ensureListener();
        pendingExportJson = json;
        a.runOnUiThread(new Runnable() {
            public void run() {
                try {
                    Intent i = new Intent("android.intent.action.CREATE_DOCUMENT");
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("application/gzip");
                    i.putExtra(Intent.EXTRA_TITLE, "daju-save-" + System.currentTimeMillis() + ".json.gz");
                    a.startActivityForResult(i, REQ_EXPORT);
                } catch (Throwable t) {
                    Log.e("ProfileBridge", "export picker failed", t);
                    eval("window.onDajuSaveExported && window.onDajuSaveExported(false,'无法打开保存窗口')");
                }
            }
        });
    }

    public static void importSave() {
        final Activity a = activity();
        if (a == null) return;
        ensureListener();
        a.runOnUiThread(new Runnable() {
            public void run() {
                try {
                    Intent i = new Intent("android.intent.action.OPEN_DOCUMENT");
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("*/*");
                    a.startActivityForResult(i, REQ_IMPORT);
                } catch (Throwable t) {
                    Log.e("ProfileBridge", "import picker failed", t);
                    eval("window.onDajuSaveImportError && window.onDajuSaveImportError('无法打开文件选择器')");
                }
            }
        });
    }

    private static void writeGzip(Activity a, Uri uri) throws Exception {
        if (pendingExportJson == null) throw new Exception("没有待写出的存档");
        OutputStream os = a.getContentResolver().openOutputStream(uri);
        if (os == null) throw new Exception("无法写入文件");
        GZIPOutputStream gz = new GZIPOutputStream(os);
        gz.write(pendingExportJson.getBytes("UTF-8"));
        gz.close();
        os.close();
        pendingExportJson = null;
        Toast.makeText(a, "存档已导出", Toast.LENGTH_SHORT).show();
        eval("window.onDajuSaveExported && window.onDajuSaveExported(true,'')");
    }

    private static void readGzip(Activity a, Uri uri) throws Exception {
        InputStream is = a.getContentResolver().openInputStream(uri);
        if (is == null) throw new Exception("无法读取文件");
        GZIPInputStream gz = new GZIPInputStream(is);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while ((n = gz.read(buf)) > 0) bos.write(buf, 0, n);
        gz.close();
        is.close();
        String text = new String(bos.toByteArray(), "UTF-8");
        eval("window.onDajuSaveImported && window.onDajuSaveImported('" + esc(text) + "')");
    }

    private static void ensureListener() {
        if (instance != null) return;
        instance = new ProfileBridge();
        try {
            Class<?> c = Class.forName("org.cocos2dx.lib.Cocos2dxHelper");
            Method m = c.getMethod("addOnActivityResultListener", PreferenceManager.OnActivityResultListener.class);
            m.invoke(null, instance);
        } catch (Throwable ignored) {
        }
    }

    public static int getBatteryLevel() {
        try {
            Activity a = activity();
            if (a == null) return 100;
            Intent i = a.registerReceiver(null, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
            if (i == null) return 100;
            int level = i.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
            int scale = i.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
            if (level < 0 || scale <= 0) return 100;
            return Math.max(0, Math.min(100, level * 100 / scale));
        } catch (Throwable t) {
            return 100;
        }
    }

    public static void pickAvatar() {
        Activity a = activity();
        if (a == null) return;
        ensureListener();
        try {
            Intent i = new Intent(Intent.ACTION_GET_CONTENT);
            i.setType("image/*");
            i.addCategory(Intent.CATEGORY_OPENABLE);
            a.startActivityForResult(i, 1001);
            Log.e("ProfileBridge", "picker started");
        } catch (Throwable t) {
            Log.e("ProfileBridge", "picker failed", t);
        }
    }

    public boolean onActivityResult(int requestCode, int resultCode, Intent data) {
        Log.e("ProfileBridge", "onActivityResult req=" + requestCode + " res=" + resultCode + " data=" + data);
        if (requestCode == REQ_EXPORT) {
            if (resultCode != Activity.RESULT_OK || data == null || data.getData() == null) return false;
            try {
                writeGzip(activity(), data.getData());
                return true;
            } catch (Throwable t) {
                Log.e("ProfileBridge", "export failed", t);
                Toast.makeText(activity(), "存档导出失败", Toast.LENGTH_SHORT).show();
                eval("window.onDajuSaveExported && window.onDajuSaveExported(false,'存档导出失败')");
                return false;
            }
        }
        if (requestCode == REQ_IMPORT) {
            if (resultCode != Activity.RESULT_OK || data == null || data.getData() == null) return false;
            try {
                readGzip(activity(), data.getData());
                return true;
            } catch (Throwable t) {
                Log.e("ProfileBridge", "import failed", t);
                Toast.makeText(activity(), "存档读取失败", Toast.LENGTH_SHORT).show();
                eval("window.onDajuSaveImportError && window.onDajuSaveImportError('存档读取失败')");
                return false;
            }
        }
        if (requestCode != REQ_AVATAR) return false;
        if (resultCode != Activity.RESULT_OK || data == null) return false;
        Activity act0 = activity();
        if (act0 != null) {
            Toast.makeText(act0, "收到图片，正在裁剪", Toast.LENGTH_SHORT).show();
        }
        Uri picked = data.getData();
        if (picked == null && data.getClipData() != null && data.getClipData().getItemCount() > 0) {
            picked = data.getClipData().getItemAt(0).getUri();
        }
        if (picked == null) return false;
        InputStream in = null;
        FileOutputStream out = null;
        try {
            Activity a = activity();
            if (a == null) return false;
            Uri uri = picked;
            in = a.getContentResolver().openInputStream(uri);
            Bitmap src = BitmapFactory.decodeStream(in);
            if (src == null) return false;
            int w = src.getWidth();
            int h = src.getHeight();
            int size = Math.min(w, h);
            Bitmap crop = Bitmap.createBitmap(src, (w - size) / 2, (h - size) / 2, size, size);
            Bitmap result = Bitmap.createScaledBitmap(crop, 256, 256, true);
            File f = new File(a.getFilesDir(), "profile_avatar_" + System.currentTimeMillis() + ".png");
            out = new FileOutputStream(f);
            result.compress(Bitmap.CompressFormat.PNG, 100, out);
            out.close();
            out = null;
            Toast.makeText(a, "头像已裁剪: " + f.getName(), Toast.LENGTH_SHORT).show();
            Log.e("ProfileBridge", "saved avatar: " + f.getAbsolutePath());
            eval("window.onNativeAvatar && window.onNativeAvatar('" + esc(f.getAbsolutePath()) + "')");
            return true;
        } catch (Throwable t) {
            Log.e("ProfileBridge", "crop failed", t);
            if (activity() != null) Toast.makeText(activity(), "裁剪失败", Toast.LENGTH_SHORT).show();
            return false;
        } finally {
            try { if (in != null) in.close(); } catch (Throwable ignored) {}
            try { if (out != null) out.close(); } catch (Throwable ignored) {}
        }
    }
}
