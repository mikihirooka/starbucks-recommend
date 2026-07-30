import pandas as pd
import streamlit as st


# ==========================================
# ページ設定
# ==========================================

st.set_page_config(
    page_title="今日のスタバ、何にする？",
    page_icon="☕",
    layout="centered",
)

st.title("☕ 今日のスタバ、何にする？")

st.caption(
    "気分や好みから、おすすめのドリンクと"
    "カスタマイズを提案します。"
)


# ==========================================
# データの読み込み
# ==========================================

@st.cache_data
def load_data():
    """
    drinks.csvを読み込む。
    """
    return pd.read_csv("drinks.csv")


try:
    drinks = load_data()

except FileNotFoundError:
    st.error(
        "drinks.csvが見つかりません。"
        "app.pyと同じフォルダに保存してください。"
    )
    st.stop()

except Exception as error:
    st.error(
        f"データの読み込み中にエラーが発生しました：{error}"
    )
    st.stop()


# ==========================================
# 共通処理
# ==========================================

def split_options(value):
    """
    CSV内の「|」で区切られた文字列を
    Pythonのリストへ変換する。

    例：
    "豆乳|オーツミルク"
    ↓
    ["豆乳", "オーツミルク"]
    """

    if pd.isna(value):
        return []

    value = str(value).strip()

    if value == "":
        return []

    if value == "なし":
        return []

    return [
        item.strip()
        for item in value.split("|")
        if item.strip()
    ]


def clamp_score(score, minimum=0):
    """
    スコアが最低値より小さくならないようにする。
    """
    return max(score, minimum)


# ==========================================
# 1．ドリンクの希望
# ==========================================

st.markdown("## 1．飲みたいドリンクを選ぶ")


temperature = st.radio(
    "温度は？",
    [
        "ホット",
        "アイス",
        "どちらでも",
    ],
    horizontal=True,
)


drink_type = st.selectbox(
    "どんなタイプが飲みたい？",
    [
        "コーヒー",
        "ティー",
        "フラペチーノ",
        "その他",
        "どれでも",
    ],
)


tea_type = "指定なし"

if drink_type == "ティー":

    tea_type = st.selectbox(
        "好きなティーのタイプは？",
        [
            "紅茶系",
            "抹茶系",
            "ほうじ茶系",
            "フルーツ系",
            "ハーブ系",
            "指定なし",
        ],
    )


sweetness_labels = {
    0: "甘さなし",
    1: "かなり控えめ",
    2: "控えめ",
    3: "普通",
    4: "甘め",
    5: "かなり甘め",
}


sweetness = st.select_slider(
    "甘さはどれくらいがいい？",
    options=[0, 1, 2, 3, 4, 5],
    value=3,
    format_func=lambda value: sweetness_labels[value],
)


richness_labels = {
    1: "かなりさっぱり",
    2: "さっぱり",
    3: "ほどほど",
    4: "濃厚",
    5: "かなり濃厚",
}


richness = st.select_slider(
    "味わいは？",
    options=[1, 2, 3, 4, 5],
    value=3,
    format_func=lambda value: richness_labels[value],
)


milk_level = st.selectbox(
    "ミルク感は？",
    [
        "なし",
        "少なめ",
        "ほどほど",
        "しっかり",
        "気にしない",
    ],
)


caffeine = st.selectbox(
    "カフェインは？",
    [
        "あり",
        "なし",
        "気にしない",
    ],
)


mood = st.selectbox(
    "今の気分は？",
    [
        "ひと息つきたい",
        "目を覚ましたい",
        "甘いもので満たされたい",
        "さっぱりしたい",
        "ちょっと冒険したい",
    ],
)


# ==========================================
# 2．カスタマイズの希望
# ==========================================

st.markdown("## 2．カスタマイズの希望")


customize_preference = st.radio(
    "カスタマイズはどうする？",
    [
        "おすすめしてほしい",
        "自分で希望を選ぶ",
        "カスタマイズなし",
    ],
)


custom_sweetness = "変更なし"
custom_milk = "変更なし"
custom_extra = "変更なし"


if customize_preference == "自分で希望を選ぶ":

    custom_sweetness = st.selectbox(
        "甘さのカスタマイズ",
        [
            "変更なし",
            "甘さなし",
            "甘さ控えめ",
            "甘め",
        ],
    )

    custom_milk = st.selectbox(
        "ミルクのカスタマイズ",
        [
            "変更なし",
            "低脂肪タイプ",
            "無脂肪タイプ",
            "豆乳",
            "アーモンドミルク",
            "オーツミルク",
        ],
    )

    custom_extra = st.selectbox(
        "追加したいもの",
        [
            "変更なし",
            "ホイップ",
            "チョコレートソース",
            "キャラメルソース",
            "はちみつ",
            "シナモン",
            "パウダー多め",
        ],
    )


# ==========================================
# ドリンクのスコア計算
# ==========================================

milk_map = {
    "なし": 0,
    "少なめ": 1,
    "ほどほど": 3,
    "しっかり": 5,
}


def temperature_score(row):
    """
    希望する温度と、商品の対応温度を比較する。
    """

    if temperature == "どちらでも":
        return 1

    available_temperatures = split_options(
        row["temperature"]
    )

    if temperature in available_temperatures:
        return 5

    return -8


def category_score(row):
    """
    希望するドリンクの種類を比較する。
    """

    if drink_type == "どれでも":
        return 1

    if row["category"] == drink_type:
        return 6

    return -4


def tea_type_score(row):
    """
    ティーを選んだ場合のみ、
    ティーの種類を比較する。
    """

    if drink_type != "ティー":
        return 0

    if tea_type == "指定なし":
        return 0

    if row["tea_type"] == tea_type:
        return 5

    return -3


def caffeine_score(row):
    """
    カフェインの希望を比較する。
    """

    if caffeine == "気にしない":
        return 0

    if row["caffeine"] == caffeine:
        return 5

    return -8


def sweetness_score(row):
    """
    甘さの希望と、商品の甘さの差を評価する。
    差が小さいほど高得点。
    """

    drink_sweetness = int(
        row["sweetness"]
    )

    difference = abs(
        drink_sweetness - sweetness
    )

    return clamp_score(
        6 - difference * 2
    )


def richness_score(row):
    """
    濃厚さの希望と、商品の濃厚さの差を評価する。
    """

    drink_richness = int(
        row["richness"]
    )

    difference = abs(
        drink_richness - richness
    )

    return clamp_score(
        5 - difference
    )


def milk_score(row):
    """
    ミルク感の希望と、商品のミルク感を比較する。
    """

    if milk_level == "気にしない":
        return 0

    selected_level = milk_map[milk_level]

    drink_level = int(
        row["milk_level"]
    )

    difference = abs(
        drink_level - selected_level
    )

    return clamp_score(
        5 - difference
    )


def mood_score(row):
    """
    商品に登録された気分と、
    利用者の気分を比較する。
    """

    available_moods = split_options(
        row["moods"]
    )

    if mood in available_moods:
        return 6

    return 0


def customization_compatibility_score(row):
    """
    利用者が希望したカスタマイズに、
    商品が対応しているかを評価する。
    """

    if customize_preference != "自分で希望を選ぶ":
        return 0

    score = 0

    available_sweetness = split_options(
        row["custom_sweetness"]
    )

    available_milk = split_options(
        row["custom_milk"]
    )

    available_extra = split_options(
        row["custom_extra"]
    )

    if custom_sweetness != "変更なし":

        if custom_sweetness in available_sweetness:
            score += 5

        else:
            score -= 7

    if custom_milk != "変更なし":

        if custom_milk in available_milk:
            score += 5

        else:
            score -= 7

    if custom_extra != "変更なし":

        if custom_extra in available_extra:
            score += 5

        else:
            score -= 7

    return score


def calculate_score(row):
    """
    各条件のスコアを合計する。
    """

    score = 0

    score += temperature_score(row)
    score += category_score(row)
    score += tea_type_score(row)
    score += caffeine_score(row)
    score += sweetness_score(row)
    score += richness_score(row)
    score += milk_score(row)
    score += mood_score(row)
    score += customization_compatibility_score(row)

    return score


# ==========================================
# カスタマイズの推薦
# ==========================================

def choose_recommended_sweetness(row):
    """
    甘さに関するカスタマイズを決める。
    """

    available = split_options(
        row["custom_sweetness"]
    )

    if not available:
        return None

    # 利用者が自分で希望を指定した場合
    if customize_preference == "自分で希望を選ぶ":

        if custom_sweetness == "変更なし":
            return None

        if custom_sweetness in available:
            return custom_sweetness

        return None

    # システムにおすすめしてもらう場合
    if sweetness == 0:

        if "甘さなし" in available:
            return "甘さなし"

        if "甘さ控えめ" in available:
            return "甘さ控えめ"

    if sweetness <= 2:

        if "甘さ控えめ" in available:
            return "甘さ控えめ"

        if "甘さなし" in available:
            return "甘さなし"

    if sweetness >= 4:

        if "甘め" in available:
            return "甘め"

    return None


def choose_recommended_milk(row):
    """
    ミルクに関するカスタマイズを決める。
    """

    available = split_options(
        row["custom_milk"]
    )

    if not available:
        return None

    # 利用者が自分で希望を指定した場合
    if customize_preference == "自分で希望を選ぶ":

        if custom_milk == "変更なし":
            return None

        if custom_milk in available:
            return custom_milk

        return None

    # システムにおすすめしてもらう場合
    if milk_level == "なし":
        return None

    if milk_level == "少なめ":

        for option in [
            "無脂肪タイプ",
            "低脂肪タイプ",
        ]:
            if option in available:
                return option

    if milk_level == "しっかり":

        for option in [
            "オーツミルク",
            "豆乳",
            "アーモンドミルク",
        ]:
            if option in available:
                return option

    if mood == "ちょっと冒険したい":

        for option in [
            "アーモンドミルク",
            "オーツミルク",
            "豆乳",
        ]:
            if option in available:
                return option

    return None


def choose_recommended_extra(row):
    """
    ソースやホイップなどの
    追加カスタマイズを決める。
    """

    available = split_options(
        row["custom_extra"]
    )

    if not available:
        return None

    # 利用者が自分で希望を指定した場合
    if customize_preference == "自分で希望を選ぶ":

        if custom_extra == "変更なし":
            return None

        if custom_extra in available:
            return custom_extra

        return None

    # 甘さなしを希望しているときは、
    # 甘い追加トッピングを避ける
    if sweetness == 0:

        for option in [
            "シナモン",
            "パウダー多め",
        ]:
            if option in available:
                return option

        return None

    if mood == "甘いもので満たされたい":

        for option in [
            "ホイップ",
            "キャラメルソース",
            "チョコレートソース",
        ]:
            if option in available:
                return option

    if mood == "ひと息つきたい":

        for option in [
            "はちみつ",
            "シナモン",
        ]:
            if option in available:
                return option

    if mood == "ちょっと冒険したい":

        for option in [
            "シナモン",
            "パウダー多め",
            "キャラメルソース",
        ]:
            if option in available:
                return option

    return None


def create_customization_list(row):
    """
    推薦されたカスタマイズを
    表示用の文章としてリストにまとめる。
    """

    if customize_preference == "カスタマイズなし":
        return []

    recommendations = []

    sweet_option = choose_recommended_sweetness(row)
    milk_option = choose_recommended_milk(row)
    extra_option = choose_recommended_extra(row)

    if sweet_option == "甘さなし":

        recommendations.append(
            "甘さ：可能な範囲でシロップなどを抜く"
        )

    elif sweet_option == "甘さ控えめ":

        recommendations.append(
            "甘さ：シロップなどを少なめにする"
        )

    elif sweet_option == "甘め":

        recommendations.append(
            "甘さ：シロップなどを多めにする"
        )

    if milk_option is not None:

        recommendations.append(
            f"ミルク：{milk_option}に変更"
        )

    if extra_option is not None:

        recommendations.append(
            f"追加：{extra_option}"
        )

    return recommendations


# ==========================================
# 結果の表示
# ==========================================

def show_drink_result(row, main_result=False):
    """
    おすすめドリンクとカスタマイズを表示する。
    """

    if main_result:

        st.markdown("## 🌟 今日のおすすめ")
        st.subheader(row["name"])

    else:

        st.markdown(f"### {row['name']}")

    st.write(row["description"])

    st.markdown(
        f"**おすすめ理由：** {row['reason']}"
    )

    customizations = create_customization_list(row)

    if customize_preference == "カスタマイズなし":

        st.caption(
            "今回はカスタマイズなしでおすすめします。"
        )

    elif customizations:

        st.markdown("#### おすすめカスタマイズ")

        for customization in customizations:

            st.write(
                f"・{customization}"
            )

    else:

        st.caption(
            "このドリンクは、そのままでも希望に合っています。"
        )


# ==========================================
# 推薦ボタン
# ==========================================

if st.button(
    "今日の一杯を決める",
    type="primary",
    use_container_width=True,
):

    scored = drinks.copy()

    scored["score"] = scored.apply(
        calculate_score,
        axis=1,
    )

    scored = scored.sort_values(
        by=[
            "score",
            "name",
        ],
        ascending=[
            False,
            True,
        ],
    )

    best = scored.iloc[0]

    others = scored.iloc[1:4]

    st.divider()

    show_drink_result(
        best,
        main_result=True,
    )

    with st.expander("ほかの候補も見る"):

        for _, row in others.iterrows():

            show_drink_result(row)

            st.divider()


# ==========================================
# 注意書き
# ==========================================

st.divider()

st.caption(
    "※授業課題用の非公式アプリです。"
    "「甘さなし」は、可能な範囲でシロップなどを抜く"
    "カスタマイズを意味し、完全な無糖を保証するものではありません。"
    "商品や提供状況、カフェイン、カスタマイズの可否は、"
    "店舗や時期によって異なる場合があります。"
)