import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# 🔐 パスワード認証
PASSWORD = st.secrets.get("APP_PASSWORD", "defaultpass")
input_pwd = st.text_input("🔒 パスワードを入力してください", type="password")
if input_pwd != PASSWORD:
    st.warning("パスワードが必要です。")
    st.stop()

# 🔑 APIキーの設定
openai_api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# 📂 CSVデータ読み込み（data.csv）
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        df = df.dropna()
        df = df[df["評価値"] >= 70]  # 高評価のみ抽出
        return df
    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
        return pd.DataFrame(columns=["お題", "ボケ", "評価値"])

data_df = load_data()

# 🎯 プロンプト構築
def build_prompt(user_topic, rules, custom_rule, ref_df):
    rule_text = ""
    if rules:
        rule_text += "・" + "\n・".join(rules) + "\n"
    if custom_rule:
        rule_text += f"・{custom_rule.strip()}\n"

    # 類似お題の参考例（上位3件）
    ref_lines = []
    for i, row in ref_df.sample(min(3, len(ref_df))).iterrows():
        ref_lines.append(f"お題「{row['お題']}」に対する高評価ボケ例：{row['ボケ']}")

    examples = "\n".join(ref_lines)

    prompt = f"""
あなたは一流の大喜利芸人AIです。
以下のお題に対して、観客から高評価を得られそうなボケを5つ考えてください。

【ルール】
{rule_text}・1ボケにつき1～2文以内

【参考ボケ（実際に高評価を得たボケ）】
{examples}

【今回のお題】
{user_topic}

【回答】
1.
2.
3.
4.
5.
"""
    return prompt

# 🔮 生成関数
def generate_bokes(user_topic, rules, custom_rule):
    prompt = build_prompt(user_topic, rules, custom_rule, data_df)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.95
    )
    result = response.choices[0].message.content

    bokes = []
    for line in result.splitlines():
        if line.strip().startswith(tuple("12345")):
            boke = line.split('.', 1)[-1].strip()
            if boke:
                bokes.append(boke)
    return bokes

# --- Streamlit UI ---
st.title("🎭 AI大喜利：データ活用ボケ生成")

topic = st.text_input("🎤 お題を入力してください", "")

st.subheader("🎨 ボケのルール（複数選択可）")
rule_options = [
        "センス良くする",
        "短めの回答",
        "テンポと落ちを重視する",
        "意外性を取り入れる",
        "シュールにする",
        "毒舌ブラックにする",
        "かわいさを加える",
        "ツッコミ風の一文にする"
]
selected_rules = st.multiselect("使いたいルールを選んでください", rule_options)
custom_rule = st.text_input("📝 独自のルールがあれば入力してください")

if st.button("ボケを生成！") and topic:
    with st.spinner("生成中..."):
        bokes = generate_bokes(topic, selected_rules, custom_rule)
        st.success("🎯 生成されたボケ")
        for i, b in enumerate(bokes, 1):
            st.markdown(f"**{i}.** {b}")
