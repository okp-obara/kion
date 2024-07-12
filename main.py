import pandas as pd
import requests
import os
from io import StringIO

# 気象庁の最新気温データのURL
url = "https://www.data.jma.go.jp/stats/data/mdrr/tem_rct/alltable/mxtemsadext00_rct.csv"

# データを取得
response = requests.get(url)
response.encoding = 'shift_jis'  # 日本語文字コードの設定
data = StringIO(response.text)

# データをpandasデータフレームとして読み込み
df = pd.read_csv(data)

# データを保存 ローカルで確認する用
# file_path = "temperature_data.csv"
# df.to_csv(file_path, index=False)

# 特定の場所の気温を抽出
location = "東京（トウキョウ）"
temperature_data = df[df['地点'] == location]

# 指定時間の温度を取得
day=temperature_data['現在時刻(日)'].values[0]
temperature = temperature_data[f'{day}日の最高気温(℃)'].values[0]
print(f"{day}日の最高気温(℃): {temperature}")

# 取得タイミング
timing=f'{temperature_data['現在時刻(年)'].values[0]}年{temperature_data['現在時刻(月)'].values[0]}月{temperature_data['現在時刻(日)'].values[0]}日{temperature_data['現在時刻(時)'].values[0]}時{temperature_data['現在時刻(分)'].values[0]}分 計測'
temperature_info=f'{temperature}度@{timing}'
print(temperature_info)

# ジャッジ
judgement_temperature=27.0


# テキストの整形
comment=''
if temperature > 30:
    comment = "本日は在宅作業よ。屋内でも熱中症になることも多いから、気を付けて。"
elif temperature > judgement_temperature:
    comment = "ハァ……暑すぎ。今日は在宅作業をオススメするけど。"
else:
    comment = "本日は出社日よ。水分をこまめに摂って、出社中の熱中症には十分気を付けて。"

# slack
slack_data = {'text': f"おはようございます\n{comment}\n\n{temperature_info}" }

slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

response = requests.post(
    slack_webhook_url, json=slack_data,
    headers={'Content-Type': 'application/json'}
)

if response.status_code != 200:
    raise ValueError(
        f'Request to slack returned an error {response.status_code}, the response is:\n{response.text}'
    )
else:
    print("メッセージが送信されました。")


