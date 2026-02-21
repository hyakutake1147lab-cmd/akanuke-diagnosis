import os
import base64
import json
from pathlib import Path

import streamlit as st
from openai import OpenAI

# =====================
# ページ設定
# =====================
st.set_page_config(
    page_title="AI垢抜け診断",
    page_icon="✨",
    layout="centered"
)

# =====================
# カスタムCSS
# =====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;500;700&family=Shippori+Mincho:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Zen Maru Gothic', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #fdf6f0 0%, #fce8e8 50%, #f0e8fd 100%);
    min-height: 100vh;
}

h1, h2, h3 {
    font-family: 'Shippori Mincho', serif;
}

.hero-title {
    font-family: 'Shippori Mincho', serif;
    font-size: 2.4rem;
    font-weight: 600;
    color: #2d1b2e;
    text-align: center;
    letter-spacing: 0.05em;
    line-height: 1.4;
    margin-bottom: 0.3rem;
}

.hero-sub {
    text-align: center;
    color: #8b6a7a;
    font-size: 0.95rem;
    margin-bottom: 2rem;
    letter-spacing: 0.08em;
}

.card {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(12px);
    border-radius: 20px;
    padding: 1.8rem 2rem;
    margin: 1rem 0;
    border: 1px solid rgba(255,200,210,0.4);
    box-shadow: 0 4px 24px rgba(180,120,140,0.08);
}

.result-header {
    font-family: 'Shippori Mincho', serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #2d1b2e;
    margin-bottom: 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #f5c5d0;
}

.tag {
    display: inline-block;
    background: #fce8f0;
    color: #c4647a;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.82rem;
    margin: 0.2rem;
    border: 1px solid #f0b8c8;
}

.tag-bad {
    background: #f0f0f0;
    color: #888;
    border-color: #ddd;
}

.point-box {
    background: linear-gradient(135deg, #fff0f5, #f5eeff);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    border-left: 4px solid #e8879a;
    margin-top: 0.8rem;
    font-size: 0.95rem;
    color: #3d2030;
    line-height: 1.7;
}

.season-badge {
    display: inline-block;
    background: linear-gradient(135deg, #e8879a, #c87dd4);
    color: white;
    border-radius: 30px;
    padding: 0.3rem 1.2rem;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}

.skeleton-badge {
    display: inline-block;
    background: linear-gradient(135deg, #f5a0b0, #d4a0e8);
    color: white;
    border-radius: 30px;
    padding: 0.3rem 1.2rem;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}

.upload-hint {
    text-align: center;
    color: #b08090;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}

.stButton > button {
    background: linear-gradient(135deg, #e8879a 0%, #c87dd4 100%);
    color: white;
    border: none;
    border-radius: 30px;
    padding: 0.7rem 2.5rem;
    font-family: 'Zen Maru Gothic', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(200,125,212,0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(200,125,212,0.4);
}

.footer-note {
    text-align: center;
    color: #b08090;
    font-size: 0.78rem;
    margin-top: 2rem;
    line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)

# =====================
# システムプロンプト
# =====================
SYSTEM_PROMPT = """
あなたはプロのパーソナルスタイリスト兼美容アドバイザーです。
提供された顔写真を丁寧に分析し、以下の3項目を日本語で診断してください。

出力はJSON形式で以下の構造にしてください：
{
  "骨格タイプ": {
    "タイプ": "ストレート/ウェーブ/ナチュラルのいずれか",
    "特徴": "その人の特徴の説明（2〜3文）",
    "似合うスタイル": ["アイテム1", "アイテム2", "アイテム3"],
    "避けるべきスタイル": ["アイテム1", "アイテム2"]
  },
  "パーソナルカラー": {
    "シーズン": "Spring/Summer/Autumn/Winterのいずれか",
    "説明": "なぜそのシーズンか（2〜3文）",
    "似合う色": ["色1", "色2", "色3", "色4"],
    "避けるべき色": ["色1", "色2"],
    "おすすめリップカラー": "具体的な色"
  },
  "メイク提案": {
    "全体コンセプト": "メイクの方向性（1文）",
    "ベースメイク": "肌感・カバー感のアドバイス",
    "アイメイク": "具体的な方法と色",
    "チーク": "色と入れ方",
    "リップ": "色と質感",
    "垢抜けポイント": "今すぐ取り入れられる最重要アドバイス（1〜2文）"
  }
}

写真が不鮮明な場合でも、見える範囲で最大限分析し、推測で構いませんので必ず具体的・断定的に診断してください。
「判断が難しい」「写真から判断できない」という回答は絶対に避け、常に断言してください。
必ずJSON形式のみで返答し、前後に余分なテキストを一切含めないでください。
"""


def diagnose(image_bytes: bytes, media_type: str, api_key: str) -> dict:
    client = OpenAI(api_key=api_key)
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{b64}",
                            "detail": "high"
                        }
                    },
                    {"type": "text", "text": "診断してください。JSONのみで返答してください。"}
                ]
            }
        ],
        max_tokens=1500,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content.strip()
    return json.loads(content)


def render_results(result: dict):
    k = result.get("骨格タイプ", {})
    p = result.get("パーソナルカラー", {})
    m = result.get("メイク提案", {})

    # 骨格タイプ
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="result-header">🦴 骨格タイプ</div>', unsafe_allow_html=True)
    st.markdown(f'<span class="skeleton-badge">{k.get("タイプ", "")}</span>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#4a3040;font-size:0.9rem;line-height:1.8;">{k.get("特徴", "")}</p>', unsafe_allow_html=True)

    good = "".join([f'<span class="tag">✅ {i}</span>' for i in k.get("似合うスタイル", [])])
    bad = "".join([f'<span class="tag tag-bad">❌ {i}</span>' for i in k.get("避けるべきスタイル", [])])
    st.markdown(f'<div>{good}{bad}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # パーソナルカラー
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="result-header">🎨 パーソナルカラー</div>', unsafe_allow_html=True)
    st.markdown(f'<span class="season-badge">{p.get("シーズン", "")}</span>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#4a3040;font-size:0.9rem;line-height:1.8;">{p.get("説明", "")}</p>', unsafe_allow_html=True)

    good_c = "".join([f'<span class="tag">✅ {i}</span>' for i in p.get("似合う色", [])])
    bad_c = "".join([f'<span class="tag tag-bad">❌ {i}</span>' for i in p.get("避けるべき色", [])])
    st.markdown(f'<div>{good_c}{bad_c}</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="margin-top:0.8rem;color:#4a3040;font-size:0.9rem;">💄 おすすめリップ：<strong>{p.get("おすすめリップカラー", "")}</strong></p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # メイク提案
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="result-header">💄 メイク提案</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#4a3040;font-size:0.9rem;font-weight:600;">{m.get("全体コンセプト", "")}</p>', unsafe_allow_html=True)

    details = [
        ("🌸 ベースメイク", m.get("ベースメイク", "")),
        ("👁 アイメイク", m.get("アイメイク", "")),
        ("🌷 チーク", m.get("チーク", "")),
        ("💋 リップ", m.get("リップ", "")),
    ]
    for label, val in details:
        st.markdown(f'<p style="color:#6a4a5a;font-size:0.88rem;margin:0.3rem 0;"><strong>{label}</strong>：{val}</p>', unsafe_allow_html=True)

    st.markdown(f'<div class="point-box">⭐ <strong>垢抜けポイント</strong><br>{m.get("垢抜けポイント", "")}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# =====================
# メインUI
# =====================
st.markdown('<h1 class="hero-title">✨ AI 垢抜け診断</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">骨格 × パーソナルカラー × メイク提案を無料で</p>', unsafe_allow_html=True)

# APIキー入力
with st.expander("🔑 OpenAI APIキーを入力（必須）"):
    api_key = st.text_input("APIキー", type="password", placeholder="sk-...", key="api_key")
    st.markdown('<p style="color:#b08090;font-size:0.8rem;">キーはサーバーに保存されません。セッション内のみ使用されます。</p>', unsafe_allow_html=True)

# 画像アップロード
uploaded = st.file_uploader("📸 顔写真をアップロード", type=["jpg", "jpeg", "png", "webp"])
st.markdown('<p class="upload-hint">正面顔・明るい場所・首元まで映っている写真が最も精度が高いです</p>', unsafe_allow_html=True)

if uploaded:
    st.image(uploaded, caption="アップロードされた写真", use_column_width=True)

# 診断ボタン
if st.button("診断スタート ✨"):
    if not api_key:
        st.error("OpenAI APIキーを入力してください")
    elif not uploaded:
        st.error("顔写真をアップロードしてください")
    else:
        ext = Path(uploaded.name).suffix.lower()
        media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        media_type = media_map.get(ext, "image/jpeg")

        with st.spinner("🔍 AIが分析中です...少々お待ちください"):
            try:
                result = diagnose(uploaded.read(), media_type, api_key)
                st.success("診断完了！")
                render_results(result)

                # JSON保存ボタン
                st.download_button(
                    label="📥 結果をJSONで保存",
                    data=json.dumps(result, ensure_ascii=False, indent=2),
                    file_name="akaнuke_result.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

st.markdown("""
<div class="footer-note">
  このアプリはGPT-4oを使用しています。診断結果はAIによる推測であり、<br>
  プロの診断の代替を保証するものではありません。
</div>
""", unsafe_allow_html=True)
