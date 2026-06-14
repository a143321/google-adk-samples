# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import requests

import google.auth
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ.get(
    "GOOGLE_CLOUD_LOCATION", "asia-northeast1"
)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# --- プロンプト用制約・要件テンプレート ---
WEATHER_REQUIREMENTS = """【気象・天候情報に関する検索の場合 — 必須の回答項目】
1. ■ 直近3日間の天気予報（天気、降水確率、最低気温、最高気温）
2. ■ 現在発表されている特別警報、警報、注意報（あればその種類と内容、なければ「特になし」）
3. ■ 大雨や大雪などの重大な気象警報が発令されている場合、観光地へのアクセスや交通機関（JR、フライト、高速道路など）への運行・規制影響やその見込み"""

FOOD_REQUIREMENTS = """【飲食店・グルメ検索の場合 — 必須の回答項目】
1. ■ 店舗名・ジャンル（例: ジンギスカン、スープカレーなど）
2. ■ 住所・アクセス方法
3. ■ 営業時間・定休日
4. ■ 予算目安（ランチ/ディナー）
5. ■ おすすめメニューや特徴、口コミでの評価・雰囲気
6. ■ 事前予約の推奨度（混雑状況）
7. ■ 情報源（参照したWebサイト名やURL）"""

ACCOMMODATION_REQUIREMENTS = """【宿泊施設検索の場合 — 必須の回答項目】
1. ■ 施設名・タイプ（ホテル、旅館、温泉宿など）
2. ■ 住所・アクセス方法（送迎バスの有無など）
3. ■ 客室タイプ・温泉の有無（露天風呂、客室露天など）
4. ■ 宿泊料金の目安
5. ■ おすすめポイント・食事内容・特徴
6. ■ 予約時の注意点や推奨度
7. ■ 情報源（参照したWebサイト名やURL）"""


# 記憶を Memory Bank に保存するコールバック関数
async def generate_memories_callback(callback_context: CallbackContext):
    """エージェントの応答完了後に、直近の会話を Memory Bank に送信する"""
    try:
        await callback_context.add_events_to_memory(
            events=callback_context.session.events[-5:-1]
        )
    except ValueError as e:
        import logging

        logging.warning(f"Memory Bank is not available: {e}")
    except Exception as e:
        import logging

        logging.error(f"Unexpected error saving to Memory Bank: {e}")
    return None


# 都道府県・地域に応じた天気を外部の公開気象APIから取得する関数
def get_jma_weather(location: str) -> dict:
    """日本全国の指定された都道府県や主要地域（東京、長野、札幌など）のリアルタイム天気予報を取得します。

    Args:
        location: 天気を調べる日本の都市・市区町村名（例: 「札幌」や「Sapporo」など）
    """
    import requests
    import logging

    # 日本の都道府県・主要地域と気象庁（JMA）エリアコードおよび詳細エリアのマッピング
    city_to_jma = {
        "札幌": {"code": "016000", "weather_area": "石狩地方", "temp_area": "札幌"},
        "さっぽろ": {"code": "016000", "weather_area": "石狩地方", "temp_area": "札幌"},
        "sapporo": {"code": "016000", "weather_area": "石狩地方", "temp_area": "札幌"},
        "小樽": {"code": "016000", "weather_area": "後志地方", "temp_area": "倶知安"},
        "おたる": {"code": "016000", "weather_area": "後志地方", "temp_area": "倶知安"},
        "otaru": {"code": "016000", "weather_area": "後志地方", "temp_area": "倶知安"},
        "千歳": {"code": "016000", "weather_area": "石狩地方", "temp_area": "札幌"},
        "ちとせ": {"code": "016000", "weather_area": "石狩地方", "temp_area": "札幌"},
        "chitose": {"code": "016000", "weather_area": "石狩地方", "temp_area": "札幌"},
        "函館": {"code": "017000", "weather_area": "渡島地方", "temp_area": "函館"},
        "はこだて": {"code": "017000", "weather_area": "渡島地方", "temp_area": "函館"},
        "hakodate": {"code": "017000", "weather_area": "渡島地方", "temp_area": "函館"},
        "旭川": {"code": "012000", "weather_area": "上川地方", "temp_area": "旭川"},
        "あさひかわ": {
            "code": "012000",
            "weather_area": "上川地方",
            "temp_area": "旭川",
        },
        "asahikawa": {
            "code": "012000",
            "weather_area": "上川地方",
            "temp_area": "旭川",
        },
        "富良野": {"code": "012000", "weather_area": "上川地方", "temp_area": "旭川"},
        "ふらの": {"code": "012000", "weather_area": "上川地方", "temp_area": "旭川"},
        "furano": {"code": "012000", "weather_area": "上川地方", "temp_area": "旭川"},
        "美瑛": {"code": "012000", "weather_area": "上川地方", "temp_area": "旭川"},
        "びえい": {"code": "012000", "weather_area": "上川地方", "temp_area": "旭川"},
        "biei": {"code": "012000", "weather_area": "上川地方", "temp_area": "旭川"},
        "釧路": {"code": "014100", "weather_area": "釧路地方", "temp_area": "釧路"},
        "くしろ": {"code": "014100", "weather_area": "釧路地方", "temp_area": "釧路"},
        "kushiro": {"code": "014100", "weather_area": "釧路地方", "temp_area": "釧路"},
        "室蘭": {"code": "015000", "weather_area": "胆振地方", "temp_area": "室蘭"},
        "むろらん": {"code": "015000", "weather_area": "胆振地方", "temp_area": "室蘭"},
        "muroran": {"code": "015000", "weather_area": "胆振地方", "temp_area": "室蘭"},
        "登別": {"code": "015000", "weather_area": "胆振地方", "temp_area": "室蘭"},
        "のぼりべつ": {
            "code": "015000",
            "weather_area": "胆振地方",
            "temp_area": "室蘭",
        },
        "noboribetsu": {
            "code": "015000",
            "weather_area": "胆振地方",
            "temp_area": "室蘭",
        },
        "洞爺湖": {"code": "015000", "weather_area": "胆振地方", "temp_area": "室蘭"},
        "とうやこ": {"code": "015000", "weather_area": "胆振地方", "temp_area": "室蘭"},
        "toyako": {"code": "015000", "weather_area": "胆振地方", "temp_area": "室蘭"},
        "帯広": {"code": "014100", "weather_area": "十勝地方", "temp_area": "帯広"},
        "おびひろ": {"code": "014100", "weather_area": "十勝地方", "temp_area": "帯広"},
        "obihiro": {"code": "014100", "weather_area": "十勝地方", "temp_area": "帯広"},
        "北見": {"code": "013000", "weather_area": "北見地方", "temp_area": "北見"},
        "きたみ": {"code": "013000", "weather_area": "北見地方", "temp_area": "北見"},
        "kitami": {"code": "013000", "weather_area": "北見地方", "temp_area": "北見"},
        "網走": {"code": "013000", "weather_area": "網走地方", "temp_area": "網走"},
        "あばしり": {"code": "013000", "weather_area": "網走地方", "temp_area": "網走"},
        "abashiri": {"code": "013000", "weather_area": "網走地方", "temp_area": "網走"},
        "知床": {"code": "013000", "weather_area": "網走地方", "temp_area": "網走"},
        "しれとこ": {"code": "013000", "weather_area": "網走地方", "temp_area": "網走"},
        "shiretoko": {
            "code": "013000",
            "weather_area": "網走地方",
            "temp_area": "網走",
        },
        "稚内": {"code": "011000", "weather_area": "宗谷地方", "temp_area": "稚内"},
        "わっかない": {
            "code": "011000",
            "weather_area": "宗谷地方",
            "temp_area": "稚内",
        },
        "wakkanai": {"code": "011000", "weather_area": "宗谷地方", "temp_area": "稚内"},
        "青森": {"code": "020000", "weather_area": "津軽", "temp_area": "青森"},
        "青森県": {"code": "020000", "weather_area": "津軽", "temp_area": "青森"},
        "あおもり": {"code": "020000", "weather_area": "津軽", "temp_area": "青森"},
        "aomori": {"code": "020000", "weather_area": "津軽", "temp_area": "青森"},
        "岩手": {"code": "030000", "weather_area": "内陸", "temp_area": "盛岡"},
        "岩手県": {"code": "030000", "weather_area": "内陸", "temp_area": "盛岡"},
        "いわて": {"code": "030000", "weather_area": "内陸", "temp_area": "盛岡"},
        "iwate": {"code": "030000", "weather_area": "内陸", "temp_area": "盛岡"},
        "宮城": {"code": "040000", "weather_area": "東部", "temp_area": "仙台"},
        "宮城県": {"code": "040000", "weather_area": "東部", "temp_area": "仙台"},
        "みやぎ": {"code": "040000", "weather_area": "東部", "temp_area": "仙台"},
        "miyagi": {"code": "040000", "weather_area": "東部", "temp_area": "仙台"},
        "秋田": {"code": "050000", "weather_area": "沿岸", "temp_area": "秋田"},
        "秋田県": {"code": "050000", "weather_area": "沿岸", "temp_area": "秋田"},
        "あきた": {"code": "050000", "weather_area": "沿岸", "temp_area": "秋田"},
        "akita": {"code": "050000", "weather_area": "沿岸", "temp_area": "秋田"},
        "山形": {"code": "060000", "weather_area": "村山", "temp_area": "山形"},
        "山形県": {"code": "060000", "weather_area": "村山", "temp_area": "山形"},
        "やまがた": {"code": "060000", "weather_area": "村山", "temp_area": "山形"},
        "yamagata": {"code": "060000", "weather_area": "村山", "temp_area": "山形"},
        "福島": {"code": "070000", "weather_area": "中通り", "temp_area": "福島"},
        "福島県": {"code": "070000", "weather_area": "中通り", "temp_area": "福島"},
        "ふくしま": {"code": "070000", "weather_area": "中通り", "temp_area": "福島"},
        "fukushima": {"code": "070000", "weather_area": "中通り", "temp_area": "福島"},
        "茨城": {"code": "080000", "weather_area": "北部", "temp_area": "水戸"},
        "茨城県": {"code": "080000", "weather_area": "北部", "temp_area": "水戸"},
        "いばらき": {"code": "080000", "weather_area": "北部", "temp_area": "水戸"},
        "ibaraki": {"code": "080000", "weather_area": "北部", "temp_area": "水戸"},
        "栃木": {"code": "090000", "weather_area": "南部", "temp_area": "宇都宮"},
        "栃木県": {"code": "090000", "weather_area": "南部", "temp_area": "宇都宮"},
        "とちぎ": {"code": "090000", "weather_area": "南部", "temp_area": "宇都宮"},
        "tochigi": {"code": "090000", "weather_area": "南部", "temp_area": "宇都宮"},
        "群馬": {"code": "100000", "weather_area": "南部", "temp_area": "前橋"},
        "群馬県": {"code": "100000", "weather_area": "南部", "temp_area": "前橋"},
        "ぐんま": {"code": "100000", "weather_area": "南部", "temp_area": "前橋"},
        "gunma": {"code": "100000", "weather_area": "南部", "temp_area": "前橋"},
        "埼玉": {"code": "110000", "weather_area": "南部", "temp_area": "さいたま"},
        "埼玉県": {"code": "110000", "weather_area": "南部", "temp_area": "さいたま"},
        "さいたま": {"code": "110000", "weather_area": "南部", "temp_area": "さいたま"},
        "saitama": {"code": "110000", "weather_area": "南部", "temp_area": "さいたま"},
        "千葉": {"code": "120000", "weather_area": "北西部", "temp_area": "千葉"},
        "千葉県": {"code": "120000", "weather_area": "北西部", "temp_area": "千葉"},
        "ちば": {"code": "120000", "weather_area": "北西部", "temp_area": "千葉"},
        "chiba": {"code": "120000", "weather_area": "北西部", "temp_area": "千葉"},
        "東京": {"code": "130000", "weather_area": "東京地方", "temp_area": "東京"},
        "東京都": {"code": "130000", "weather_area": "東京地方", "temp_area": "東京"},
        "とうきょう": {
            "code": "130000",
            "weather_area": "東京地方",
            "temp_area": "東京",
        },
        "tokyo": {"code": "130000", "weather_area": "東京地方", "temp_area": "東京"},
        "神奈川": {"code": "140000", "weather_area": "東部", "temp_area": "横浜"},
        "神奈川県": {"code": "140000", "weather_area": "東部", "temp_area": "横浜"},
        "かながわ": {"code": "140000", "weather_area": "東部", "temp_area": "横浜"},
        "kanagawa": {"code": "140000", "weather_area": "東部", "temp_area": "横浜"},
        "新潟": {"code": "150000", "weather_area": "下越", "temp_area": "新潟"},
        "新潟県": {"code": "150000", "weather_area": "下越", "temp_area": "新潟"},
        "にいがた": {"code": "150000", "weather_area": "下越", "temp_area": "新潟"},
        "niigata": {"code": "150000", "weather_area": "下越", "temp_area": "新潟"},
        "富山": {"code": "160000", "weather_area": "東部", "temp_area": "富山"},
        "富山県": {"code": "160000", "weather_area": "東部", "temp_area": "富山"},
        "とやま": {"code": "160000", "weather_area": "東部", "temp_area": "富山"},
        "toyama": {"code": "160000", "weather_area": "東部", "temp_area": "富山"},
        "石川": {"code": "170000", "weather_area": "加賀", "temp_area": "金沢"},
        "石川県": {"code": "170000", "weather_area": "加賀", "temp_area": "金沢"},
        "いしかわ": {"code": "170000", "weather_area": "加賀", "temp_area": "金沢"},
        "ishikawa": {"code": "170000", "weather_area": "加賀", "temp_area": "金沢"},
        "福井": {"code": "180000", "weather_area": "嶺北", "temp_area": "福井"},
        "福井県": {"code": "180000", "weather_area": "嶺北", "temp_area": "福井"},
        "ふくい": {"code": "180000", "weather_area": "嶺北", "temp_area": "福井"},
        "fukui": {"code": "180000", "weather_area": "嶺北", "temp_area": "福井"},
        "山梨": {"code": "190000", "weather_area": "中・西部", "temp_area": "甲府"},
        "山梨県": {"code": "190000", "weather_area": "中・西部", "temp_area": "甲府"},
        "やまなし": {"code": "190000", "weather_area": "中・西部", "temp_area": "甲府"},
        "yamanashi": {
            "code": "190000",
            "weather_area": "中・西部",
            "temp_area": "甲府",
        },
        "長野": {"code": "200000", "weather_area": "北部", "temp_area": "長野"},
        "長野県": {"code": "200000", "weather_area": "北部", "temp_area": "長野"},
        "ながの": {"code": "200000", "weather_area": "北部", "temp_area": "長野"},
        "nagano": {"code": "200000", "weather_area": "北部", "temp_area": "長野"},
        "岐阜": {"code": "210000", "weather_area": "美濃地方", "temp_area": "岐阜"},
        "岐阜県": {"code": "210000", "weather_area": "美濃地方", "temp_area": "岐阜"},
        "ぎふ": {"code": "210000", "weather_area": "美濃地方", "temp_area": "岐阜"},
        "gifu": {"code": "210000", "weather_area": "美濃地方", "temp_area": "岐阜"},
        "静岡": {"code": "220000", "weather_area": "中部", "temp_area": "静岡"},
        "静岡県": {"code": "220000", "weather_area": "中部", "temp_area": "静岡"},
        "しずおか": {"code": "220000", "weather_area": "中部", "temp_area": "静岡"},
        "shizuoka": {"code": "220000", "weather_area": "中部", "temp_area": "静岡"},
        "愛知": {"code": "230000", "weather_area": "西部", "temp_area": "名古屋"},
        "愛知県": {"code": "230000", "weather_area": "西部", "temp_area": "名古屋"},
        "あいち": {"code": "230000", "weather_area": "西部", "temp_area": "名古屋"},
        "aichi": {"code": "230000", "weather_area": "西部", "temp_area": "名古屋"},
        "三重": {"code": "240000", "weather_area": "北中部", "temp_area": "津"},
        "三重県": {"code": "240000", "weather_area": "北中部", "temp_area": "津"},
        "みえ": {"code": "240000", "weather_area": "北中部", "temp_area": "津"},
        "mie": {"code": "240000", "weather_area": "北中部", "temp_area": "津"},
        "滋賀": {"code": "250000", "weather_area": "南部", "temp_area": "大津"},
        "滋賀県": {"code": "250000", "weather_area": "南部", "temp_area": "大津"},
        "しが": {"code": "250000", "weather_area": "南部", "temp_area": "大津"},
        "shiga": {"code": "250000", "weather_area": "南部", "temp_area": "大津"},
        "京都": {"code": "260000", "weather_area": "南部", "temp_area": "京都"},
        "京都府": {"code": "260000", "weather_area": "南部", "temp_area": "京都"},
        "きょうと": {"code": "260000", "weather_area": "南部", "temp_area": "京都"},
        "kyoto": {"code": "260000", "weather_area": "南部", "temp_area": "京都"},
        "大阪": {"code": "270000", "weather_area": "大阪府", "temp_area": "大阪"},
        "大阪府": {"code": "270000", "weather_area": "大阪府", "temp_area": "大阪"},
        "おおさか": {"code": "270000", "weather_area": "大阪府", "temp_area": "大阪"},
        "osaka": {"code": "270000", "weather_area": "大阪府", "temp_area": "大阪"},
        "兵庫": {"code": "280000", "weather_area": "南部", "temp_area": "神戸"},
        "兵庫県": {"code": "280000", "weather_area": "南部", "temp_area": "神戸"},
        "ひょうご": {"code": "280000", "weather_area": "南部", "temp_area": "神戸"},
        "hyogo": {"code": "280000", "weather_area": "南部", "temp_area": "神戸"},
        "奈良": {"code": "290000", "weather_area": "北部", "temp_area": "奈良"},
        "奈良県": {"code": "290000", "weather_area": "北部", "temp_area": "奈良"},
        "なら": {"code": "290000", "weather_area": "北部", "temp_area": "奈良"},
        "nara": {"code": "290000", "weather_area": "北部", "temp_area": "奈良"},
        "和歌山": {"code": "300000", "weather_area": "北部", "temp_area": "和歌山"},
        "和歌山県": {"code": "300000", "weather_area": "北部", "temp_area": "和歌山"},
        "わかやま": {"code": "300000", "weather_area": "北部", "temp_area": "和歌山"},
        "wakayama": {"code": "300000", "weather_area": "北部", "temp_area": "和歌山"},
        "鳥取": {"code": "310000", "weather_area": "東部", "temp_area": "鳥取"},
        "鳥取県": {"code": "310000", "weather_area": "東部", "temp_area": "鳥取"},
        "とっとり": {"code": "310000", "weather_area": "東部", "temp_area": "鳥取"},
        "tottori": {"code": "310000", "weather_area": "東部", "temp_area": "鳥取"},
        "島根": {"code": "320000", "weather_area": "東部", "temp_area": "松江"},
        "島根県": {"code": "320000", "weather_area": "東部", "temp_area": "松江"},
        "しまね": {"code": "320000", "weather_area": "東部", "temp_area": "松江"},
        "shimane": {"code": "320000", "weather_area": "東部", "temp_area": "松江"},
        "岡山": {"code": "330000", "weather_area": "南部", "temp_area": "岡山"},
        "岡山県": {"code": "330000", "weather_area": "南部", "temp_area": "岡山"},
        "おかやま": {"code": "330000", "weather_area": "南部", "temp_area": "岡山"},
        "okayama": {"code": "330000", "weather_area": "南部", "temp_area": "岡山"},
        "広島": {"code": "340000", "weather_area": "南部", "temp_area": "広島"},
        "広島県": {"code": "340000", "weather_area": "南部", "temp_area": "広島"},
        "ひろしま": {"code": "340000", "weather_area": "南部", "temp_area": "広島"},
        "hiroshima": {"code": "340000", "weather_area": "南部", "temp_area": "広島"},
        "山口": {"code": "350000", "weather_area": "西部", "temp_area": "下関"},
        "山口県": {"code": "350000", "weather_area": "西部", "temp_area": "下関"},
        "やまぐち": {"code": "350000", "weather_area": "西部", "temp_area": "下関"},
        "yamaguchi": {"code": "350000", "weather_area": "西部", "temp_area": "下関"},
        "徳島": {"code": "360000", "weather_area": "北部", "temp_area": "徳島"},
        "徳島県": {"code": "360000", "weather_area": "北部", "temp_area": "徳島"},
        "とくしま": {"code": "360000", "weather_area": "北部", "temp_area": "徳島"},
        "tokushima": {"code": "360000", "weather_area": "北部", "temp_area": "徳島"},
        "香川": {"code": "370000", "weather_area": "香川県", "temp_area": "高松"},
        "香川県": {"code": "370000", "weather_area": "香川県", "temp_area": "高松"},
        "かがわ": {"code": "370000", "weather_area": "香川県", "temp_area": "高松"},
        "kagawa": {"code": "370000", "weather_area": "香川県", "temp_area": "高松"},
        "愛媛": {"code": "380000", "weather_area": "中予", "temp_area": "松山"},
        "愛媛県": {"code": "380000", "weather_area": "中予", "temp_area": "松山"},
        "えひめ": {"code": "380000", "weather_area": "中予", "temp_area": "松山"},
        "ehime": {"code": "380000", "weather_area": "中予", "temp_area": "松山"},
        "高知": {"code": "390000", "weather_area": "中部", "temp_area": "高知"},
        "高知県": {"code": "390000", "weather_area": "中部", "temp_area": "高知"},
        "こうち": {"code": "390000", "weather_area": "中部", "temp_area": "高知"},
        "kochi": {"code": "390000", "weather_area": "中部", "temp_area": "高知"},
        "福岡": {"code": "400000", "weather_area": "福岡地方", "temp_area": "福岡"},
        "福岡県": {"code": "400000", "weather_area": "福岡地方", "temp_area": "福岡"},
        "ふくおか": {"code": "400000", "weather_area": "福岡地方", "temp_area": "福岡"},
        "fukuoka": {"code": "400000", "weather_area": "福岡地方", "temp_area": "福岡"},
        "佐賀": {"code": "410000", "weather_area": "南部", "temp_area": "佐賀"},
        "佐賀県": {"code": "410000", "weather_area": "南部", "temp_area": "佐賀"},
        "さが": {"code": "410000", "weather_area": "南部", "temp_area": "佐賀"},
        "saga": {"code": "410000", "weather_area": "南部", "temp_area": "佐賀"},
        "長崎": {"code": "420000", "weather_area": "南部", "temp_area": "長崎"},
        "長崎県": {"code": "420000", "weather_area": "南部", "temp_area": "長崎"},
        "ながさき": {"code": "420000", "weather_area": "南部", "temp_area": "長崎"},
        "nagasaki": {"code": "420000", "weather_area": "南部", "temp_area": "長崎"},
        "熊本": {"code": "430000", "weather_area": "熊本地方", "temp_area": "熊本"},
        "熊本県": {"code": "430000", "weather_area": "熊本地方", "temp_area": "熊本"},
        "くまもと": {"code": "430000", "weather_area": "熊本地方", "temp_area": "熊本"},
        "kumamoto": {"code": "430000", "weather_area": "熊本地方", "temp_area": "熊本"},
        "大分": {"code": "440000", "weather_area": "中部", "temp_area": "大分"},
        "大分県": {"code": "440000", "weather_area": "中部", "temp_area": "大分"},
        "おおいた": {"code": "440000", "weather_area": "中部", "temp_area": "大分"},
        "oita": {"code": "440000", "weather_area": "中部", "temp_area": "大分"},
        "宮崎": {"code": "450000", "weather_area": "南部平野部", "temp_area": "宮崎"},
        "宮崎県": {"code": "450000", "weather_area": "南部平野部", "temp_area": "宮崎"},
        "みやざき": {
            "code": "450000",
            "weather_area": "南部平野部",
            "temp_area": "宮崎",
        },
        "miyazaki": {
            "code": "450000",
            "weather_area": "南部平野部",
            "temp_area": "宮崎",
        },
        "鹿児島": {"code": "460100", "weather_area": "薩摩地方", "temp_area": "鹿児島"},
        "鹿児島県": {
            "code": "460100",
            "weather_area": "薩摩地方",
            "temp_area": "鹿児島",
        },
        "かごしま": {
            "code": "460100",
            "weather_area": "薩摩地方",
            "temp_area": "鹿児島",
        },
        "kagoshima": {
            "code": "460100",
            "weather_area": "薩摩地方",
            "temp_area": "鹿児島",
        },
        "沖縄": {"code": "471000", "weather_area": "本島中南部", "temp_area": "那覇"},
        "沖縄県": {"code": "471000", "weather_area": "本島中南部", "temp_area": "那覇"},
        "おきなわ": {
            "code": "471000",
            "weather_area": "本島中南部",
            "temp_area": "那覇",
        },
        "okinawa": {
            "code": "471000",
            "weather_area": "本島中南部",
            "temp_area": "那覇",
        },
    }

    # 入力文字列を小文字に正規化してマッチング
    loc_norm = location.strip().lower()
    jma_info = city_to_jma.get(loc_norm)
    if not jma_info:
        jma_info = city_to_jma.get(location.strip())

    if jma_info:
        try:
            area_code = jma_info["code"]
            target_weather_area = jma_info["weather_area"]
            target_temp_area = jma_info["temp_area"]

            url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            jma_data = response.json()

            publishing_office = jma_data[0].get("publishingOffice", "気象庁")
            report_time = jma_data[0].get("reportDatetime", "")

            # --- timeSeries[0]: 天気・風・波（今日/明日/明後日） ---
            time_series_weather = jma_data[0]["timeSeries"][0]
            weather_time_defines = time_series_weather.get("timeDefines", [])
            area_weather_data = None
            for area in time_series_weather["areas"]:
                if area["area"]["name"] == target_weather_area:
                    area_weather_data = area
                    break
            if not area_weather_data:
                area_weather_data = time_series_weather["areas"][0]

            area_name = area_weather_data["area"]["name"]
            weathers = area_weather_data.get("weathers", [])
            winds = area_weather_data.get("winds", [])
            waves = area_weather_data.get("waves", [])

            # 日別の天気データを構築
            daily_forecasts = []
            for i, weather in enumerate(weathers):
                day_data = {"weather": weather}
                if i < len(winds):
                    day_data["wind"] = winds[i]
                if i < len(waves):
                    day_data["wave"] = waves[i]
                if i < len(weather_time_defines):
                    day_data["date"] = weather_time_defines[i]
                daily_forecasts.append(day_data)

            # --- timeSeries[1]: 6時間ごとの降水確率 ---
            pops_data = []
            try:
                time_series_pops = jma_data[0]["timeSeries"][1]
                pops_time_defines = time_series_pops.get("timeDefines", [])
                area_pops_data = None
                for area in time_series_pops["areas"]:
                    if area["area"]["name"] == target_weather_area:
                        area_pops_data = area
                        break
                if not area_pops_data:
                    area_pops_data = time_series_pops["areas"][0]

                pops = area_pops_data.get("pops", [])
                for i, pop in enumerate(pops):
                    entry = {"probability": pop}
                    if i < len(pops_time_defines):
                        entry["time"] = pops_time_defines[i]
                    pops_data.append(entry)
            except Exception as e:
                logging.error(f"JMA POPs parsing error: {e}")

            # --- timeSeries[2]: 気温 ---
            temps = []
            temp_time_defines = []
            try:
                if len(jma_data[0]["timeSeries"]) > 2:
                    time_series_temps = jma_data[0]["timeSeries"][2]
                    temp_time_defines = time_series_temps.get("timeDefines", [])
                    area_temp_data = None
                    for area in time_series_temps["areas"]:
                        if area["area"]["name"] == target_weather_area:
                            area_temp_data = area
                            break
                    if not area_temp_data:
                        area_temp_data = time_series_temps["areas"][0]

                    temps_list = area_temp_data.get("temps", [])
                    for i, t in enumerate(temps_list):
                        entry = {"temperature": t}
                        if i < len(temp_time_defines):
                            entry["time"] = temp_time_defines[i]
                        temps.append(entry)
            except Exception as e:
                import logging
                logging.error(f"JMA Temps parsing error: {e}")

            return {
                "target_area": target_weather_area,
                "daily_forecasts": daily_forecasts,
                "pops_data": pops_data,
                "temps": temps
            }
        except Exception as e:
            import logging
            logging.error(f"JMA data fetch failed: {e}")
            return {"error": f"気象庁データの取得に失敗しました: {e}"}

    return {"error": f"{location}の気象庁エリア情報が見つかりません。"}


search_weather_agent = Agent(
    name="search_weather_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=8),
    ),
    description="Google検索で天気を調べる",
    instruction="ユーザーの指定した地域の天気を検索して簡潔に報告してください。",
    tools=[google_search]
)

weather_agent = Agent(
    name="weather_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=8),
    ),
    description="指定された地域の天気を取得するエージェント。",
    instruction="get_jma_weatherを使用して天気を取得し、情報が足りない場合はsearch_weather_agentを使用して補完してください。",
    tools=[
        get_jma_weather,
        AgentTool(agent=search_weather_agent),
    ]
)


# Web 検索用のサブエージェント
search_agent = Agent(
    name="search_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=8),
    ),
    description=(
        "Google検索で日本の観光スポット、アクティビティ、交通手段・ルート、地元の最新ニュースやイベント、天気の補足情報などを調べる。"
        "飲食店（レストラン・カフェ等）や宿泊施設（ホテル・旅館等）の検索にはこのツールを使用せず、それぞれ food_agent や accommodation_agent を使用すること。"
        "requestパラメータに検索したい内容（例: '札幌から小樽へのJR移動ルート'、'白川郷 of ライトアップイベントの日程'）を渡す。"
    ),
    instruction=f"""ユーザーの質問に対してGoogle検索を使って最新の情報を収集し、親エージェントに日本語で詳細なレポートを返してください。
検索結果から得られた情報を省略せず、具体的なデータをすべて含めてください。

【制約事項 — 必須遵守】
飲食店（レストラン、カフェ、居酒屋、名物グルメなど）の情報収集や、宿泊施設（ホテル、旅館、温泉宿など）の詳細な検索は、それぞれ専門エージェントである food_agent や accommodation_agent が担当するため、本エージェント（search_agent）では行いません。
観光地、アクティビティ、アクセスルート、交通状況、気象・天候情報など、飲食・宿泊以外の情報に絞って調査を行ってください。

{WEATHER_REQUIREMENTS}

【観光スポット・アクティビティ・交通手段に関する検索の場合 — 必須の回答項目】
1. ■ 具体的なスポット・施設名やルート（最低3件以上、または該当する主要ルート）
2. ■ 住所・アクセス方法・移動時間
3. ■ 営業時間・定休日・運行ダイヤ（わかる範囲で）
4. ■ 利用料金・入場料・交通運賃目安
5. ■ 見どころ・特徴、およびおすすめのアクティビティ・立ち寄りスポット
6. ■ 事前予約やチケット購入の要否・推奨度
7. ■ 情報源（参照したWebサイト名やURL）

※ 検索結果を自己判断で省略しないでください。具体的な数値・固有名詞・情報源を多く含めてください。""",
    tools=[google_search],
)


# グルメ検索用のサブエージェント
food_agent = Agent(
    name="food_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=8),
    ),
    description="指定された地域のおすすめグルメ、名物料理、レストラン、カフェ、居酒屋などの情報をGoogle検索で調べる。飲食店探しや食事プランの計画が必要な場合に呼び出す。引数requestに調べたい内容（例: '函館駅周辺の海鮮丼 of 美味しいお店'）を渡す。",
    instruction=f"""ユーザーの要望や指定された地域に基づいて、おすすめの飲食店や名物グルメをGoogle検索を使って詳細に調査してください。

【重要な回答数ルール】
- ユーザーから「3つ紹介して」などの具体的な件数の指定がない限り、おすすめの店舗を **1つのみ** 選定して紹介してください。

{FOOD_REQUIREMENTS}

※ 曖昧な「例：○○など」で済ませず、具体的な店舗の詳細情報を漏れなく記述してください。""",
    tools=[google_search],
)


# 宿泊施設検索用のサブエージェント
accommodation_agent = Agent(
    name="accommodation_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=8),
    ),
    description="指定された地域のおすすめ宿泊施設（ホテル、旅館、民宿、キャンプ場など）の情報をGoogle検索で調べる。宿探しや宿泊プランの計画が必要な場合に呼び出す。引数requestに調べたい内容（例: '登別温泉で露天風呂付き客室がある高級旅館'）を渡す。",
    instruction=f"""ユーザーの要望や指定された地域に基づいて、おすすめの宿泊施設をGoogle検索を使って詳細に調査してください。

【重要な回答数・選定ルール】
- ユーザーから「3つ紹介して」などの具体的な件数の指定がない限り、おすすめかつリーズナブル（予算重視）な宿泊施設を **1つのみ** 選定して紹介してください。

{ACCOMMODATION_REQUIREMENTS}

※ 曖昧な「例：○○など」で済ませず、具体的な宿の詳細情報を漏れなく記述してください。""",
    tools=[google_search],
)


# ルートエージェント（日本旅行ガイド）
root_agent = Agent(
    name="japan_guide",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=8),
    ),
    description="日本全国の旅行に関する情報を提供する総合ガイドエージェント",
    instruction="""あなたは日本旅行の専門ガイドです。

【重要：中間応答の禁止・思考プロセスの非表示】
- **ツールやサブエージェントを呼び出している情報収集フェーズの間は、ユーザーに対して一切の中間回答や会話テキスト（例：「〇〇を調べます」「次に〇〇を呼び出します」などのアナウンスや独り言）を出力しないでください。**
- **回答の中に思考プロセス、ユーザー意図の分析、ツール呼び出しの検討プロセス（例：「1. ユーザーの意図を把握」「2. ツール呼び出しの検討」「3. 回答内容の生成」などの見出しや内容）を絶対に含めないでください。ユーザー向けの実用的な旅行プランのみを直接出力してください。**
- **すべてのツールの呼び出し結果が揃った最後のターンにおいて、初めてユーザーに対する最終回答（旅行プランの全日程表）を一つのまとまったメッセージとして一度に出力してください。**

【情報取得とエージェント連携ルール】
あなた自身の内部知識（静的な学習データ）は古くなっている可能性があるため、具体的な観光プラン、グルメ情報、交通状況、宿泊、天気予報などの「具体的な調査や計画の作成」が必要な場合は、あなた自身の知識だけで回答を完結させてはなりません。必ず以下のルールに従って適切なツールを呼び出してください：

1. 旅行プランの作成、観光スポット、交通手段などの調査には、必ず `search_agent` を呼び出して最新のWeb情報を検索してください。
2. 日本国内の飲食店（レストラン、カフェ、居酒屋、郷土料理など）の具体的な情報収集には、必ず `food_agent` を呼び出して詳細な店舗情報を取得してください。
3. 日本国内の宿泊施設（ホテル、旅館、温泉宿など）の具体的な情報収集には、必ず `accommodation_agent` を呼び出して詳細な宿の情報を取得してください。
4. 「日本全国の特定の都道府県・主要都市の天気・気温」の問い合わせに対しては、必ず `weather_agent` を個別に呼び出して天気予報情報を取得してください。`weather_agent` は内部で気象庁データおよび検索のフォールバックを自動で行うため、追加で `search_agent` を使って天気を二重に検索する必要はありません。取得できた天気結果（日付、天気概況、降水確率、最低・最高気温、警報・注意報）のみをそのまま簡潔に提示してください。
5. 旅行プランやモデルコースの提案、あるいは複数地域・複数日にわたる旅行計画を作成する際は、移動や屋外アクティビティへの天候の影響を考慮するため、ユーザーから明示的な指示がない場合でも、必ず対象となるすべての地域（例: 札幌、帯広など）の天気を `weather_agent` を地域ごとに個別に呼び出して取得してください。呼び出しによって得られたフォーマット済みの天気推移テキストは、地名を混ぜ合わせて要約（例: 「札幌・帯広ともに曇り」などとまとめない）するのではなく、必ず地点ごとに独立したセクション（例: 「### 札幌の天気」「### 帯広の天気」）として、エージェントが返したフォーマットそのままプランの中に埋め込んで提示してください。服装などのアドバイスは含めないでください。また、プランに含む昼食や夕食（ランチ・ディナー等）や宿泊地については、必ず `food_agent`（最もおすすめの第一候補1店舗を選定）や `accommodation_agent`（最もおすすめかつリーズナブルな第一候補1施設を選定）を個別に呼び出して、具体的な店舗・宿の名前と詳細情報（住所、アクセス、予算、特徴、URL）をすべて含めてください。さらに、特定の主要目的地（例：知床）のみに固定するのではなく、周辺エリア（例：網走、摩周湖、阿寒など）の立ち寄りスポットや柔軟な選択肢を提案してください。また、自家用車やレンタカーでの移動の際は、往路だけでなく帰り道（復路）の交通ルートや経由道路（高速道路など）、おすすめの休憩スポット（道の駅やSA/PAなど）も省略せずに具体的に記載してください。
6. ユーザーへの回答は、必ずツールから取得した具体的な最新の調査結果に基づいて作成してください。自身で架空の情報をでっち上げたり、古い知識だけで答えたりしないでください。

【グルメ・宿泊情報の回答スタイル】
- **作成する旅行プランは、日程ごとの移動、アクティビティ、昼食や夕食、宿泊場所などをすべて含めて、全体が一目で見通せるような一つのまとまった回答（箇条書きを用いた統一されたプラン）として一度に出力してください。情報を複数のメッセージに分けたり連投したりせず、見やすく簡潔にまとめて提示してください。**
- **回答の崩れや無限ループを防ぐため、マークダウンの表形式（Table）は一切使用しないでください。すべて見出し（### 等）や箇条書きで整理してください。**
- **飲食店（ランチやディナーなど）の提案については、行程のわかりやすさと読みやすさを優先するため、各食事（1日目の昼食、1日目の夕食など）に対して第一候補（最もおすすめの1店舗）のみをプラン内に記載してください。複数の店舗候補を並べる必要はありません。**
- **宿泊施設（ホテル・旅館など）の提案については、行程のわかりやすさと読みやすさを優先するため、各日程（1日目の夜、2日目の夜など）のプラン内に、その日の最もおすすめかつリーズナブル（予算重視）な第一候補の宿泊施設（1件のみ）を記載してください。複数の宿泊施設候補を並べる必要はありません。**
- グルメ（食べ物）や宿泊場所を提案する際は、ユーザーの希望（予算、料理ジャンル、客室タイプ、温泉の有無など）に寄り添って、分かりやすいマークダウンの箇条書きで構造化して提示してください。**漠然とした案内や、単なる名前の紹介は「不完全な回答」とみなします。具体的な店舗・スポットの住所、アクセス、予算、詳細なおすすめポイント、情報源（URL）を明記してください。**

【自己紹介・機能説明の例外】
例外として、ユーザーから「あなたに何ができるか（機能やサポート内容）」「自己紹介」「あなたの役割」などについて尋ねられた場合は、ツールを呼び出す必要はありません。自身が日本旅行の専門ガイドであり、以下の機能を提供できることを親切かつ丁寧に自己紹介してください：
- 最新の観光スポットや交通ルートの検索（`search_agent` によるリアルタイムWeb検索）
- グルメやレストラン情報の検索（`food_agent` による詳細店舗検索）
- ホテルや旅館など宿泊施設の検索（`accommodation_agent` による詳細宿検索）
- 気象庁公式データによる天気・気温予報の調査（`weather_agent` による公式予報）
- 旅行の好み（旅行人数、移動手段、食事の好み、日程など）を記憶し、それに寄り添った提案を行うこと（Memory Bank機能）

ユーザーから最初の挨拶（例：「こんにちは」「はじめまして」など）や会話の始まりの入力があった際は、必ず「こんにちは！私に日本旅行の専門ガイドエージェントです。観光、グルメ、天気、移動手段などの計画をお手伝いします！」といった形で丁寧な自己紹介と挨拶を返してください。

対応できるトピック:
- 日本全国の観光スポット（札幌、小樽、函館、東京、長野、京都、大阪、沖縄など）
- 天気情報
- グルメ情報（海鮮、ラーメン、ジンギスカン、スイーツ、地元の名店、信州そばなど）
- 季節ごとのおすすめ（花見、夏の避暑、紅葉、雪まつり、スキー）
- 交通手段（JR、新幹線、レンタカー、バス、フェリー、空港アクセス）
- 温泉（登別、定山渓、別府、湯布院、草津、渋温泉など）
- 宿泊（ホテル、旅館、ペンション、キャンプ場）
- モデルコース・旅行プランの提案
- 各地の文化・歴史・伝統工芸

回答は日本語で、わかりやすく丁寧に行ってください。
ユーザーの旅行スタイルや好みに合わせた提案を心がけてください。""",
    tools=[
        AgentTool(agent=weather_agent),  # 気象専門エージェント
        AgentTool(agent=search_agent),  # 分離コンテキスト: Google検索（組み込みツール）
        AgentTool(agent=food_agent),  # グルメ専門エージェント
        AgentTool(agent=accommodation_agent),  # 宿泊専門エージェント
        PreloadMemoryTool(),  # セッション開始時に自動的に過去の記憶を読み込む
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
