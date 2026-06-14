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
import vertexai
from vertexai.types import (
    MemoryBankCustomizationConfig as CustomizationConfig,
    MemoryBankCustomizationConfigMemoryTopic as MemoryTopic,
    MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic as CustomMemoryTopic,
    MemoryBankCustomizationConfigMemoryTopicManagedMemoryTopic as ManagedMemoryTopic,
    ManagedTopicEnum,
)

client = vertexai.Client(
    project=os.getenv("PROJECT_ID"),
    location=os.getenv("LOCATION", "asia-northeast1"),
)

# Memory Bank に保存する旅行用記憶のトピック定義
memory_topics = [
    # ユーザーの一般的な好み（managed トピック）
    MemoryTopic(
        managed_memory_topic=ManagedMemoryTopic(
            managed_topic_enum=ManagedTopicEnum.USER_PREFERENCES
        )
    ),
    # 旅行の日程やペースの好み
    MemoryTopic(
        custom_memory_topic=CustomMemoryTopic(
            label="travel_itinerary_preferences",
            description=(
                "ユーザーの旅行日程（宿泊数、旅行予定時期など）および好むペース。"
                "例: 「2泊3日」、「のんびり回りたい」、「朝早くから活動したい」などのスケジュールに関する傾向。"
            ),
        )
    ),
    # グルメの嗜好・アレルギー制限
    MemoryTopic(
        custom_memory_topic=CustomMemoryTopic(
            label="dietary_preferences_and_restrictions",
            description=(
                "ユーザーが日本全国（北海道や長野など）で食べたいグルメ（ジンギスカン、海鮮、蕎麦、ラーメン、スープカレー等）、"
                "および苦手な食材やアレルギー、食事の予算やこだわり。"
            ),
        )
    ),
    # 移動手段の好み (レンタカー or 公共交通機関)
    MemoryTopic(
        custom_memory_topic=CustomMemoryTopic(
            label="transportation_preferences",
            description=(
                "旅行中の移動手段の好みや運転可否。"
                "例: 「レンタカーを運転する」、「JRやバスなどの公共交通機関だけで回る」、「徒歩中心」など。"
            ),
        )
    ),
    # 同行者・旅行スタイル
    MemoryTopic(
        custom_memory_topic=CustomMemoryTopic(
            label="companion_status_and_style",
            description=(
                "同行者の情報や旅行の目的。"
                "例: 「一人旅」、「夫婦旅行」、「小さな子供連れ」、「温泉でゆっくりしたい」、「アクティビティ重視」など。"
            ),
        )
    ),
]

customization_config = CustomizationConfig(memory_topics=memory_topics)

# 類似性検索に使用する埋め込みモデル（多言語対応の gemini-embedding-001 を指定）
project = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION", "asia-northeast1")
embedding_model = f"projects/{project}/locations/{location}/publishers/google/models/gemini-embedding-001"

# 既存の Agent Runtime を Memory Bank カスタマイズ付きで更新
resource_name = os.environ["RESOURCE_NAME"]
agent_engine = client.agent_engines.update(
    name=resource_name,
    config={
        "context_spec": {
            "memory_bank_config": {
                "customization_configs": [customization_config],
                "similarity_search_config": {
                    "embedding_model": embedding_model,
                },
            },
        },
    },
)

print("Memory Bank customization for Japan Travel Guide applied.")
print(f"Resource Name: {agent_engine.api_resource.name}")
