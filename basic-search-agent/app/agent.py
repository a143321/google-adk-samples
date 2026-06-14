# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import google_search
from google.genai import types

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ.get("GOOGLE_CLOUD_LOCATION", "asia-northeast1")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


# 最もシンプルな検索エージェント (Google検索ツールを使用)
root_agent = Agent(
    name="search_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Google検索を使用して質問（天気や時事ニュースなど）に回答するエージェント",
    instruction="""あなたは優秀なリサーチャーです。
ユーザーから最初の挨拶（例：「こんにちは」「初めまして」など）や会話の始まりの入力があった際は、必ず「こんにちは！私はGoogle検索を用いて最新情報を調べる検索アシスタントエージェントです。何について調べたいですか？」といった形で丁寧な自己紹介と挨拶を返してください。
それ以外の質問に対しては、Google検索ツールを使用して最新かつ正確な事実を調べ、日本語で簡潔に回答してください。""",
    tools=[google_search]
)

app = App(
    root_agent=root_agent,
    name="app",
)
