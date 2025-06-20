import pandas as pd
import requests
import os
from io import StringIO
from datetime import datetime
import sys

# 気象庁のCSVデータURL
JMA_URL = "https://www.data.jma.go.jp/stats/data/mdrr/tem_rct/alltable/mxtemsadext00_rct.csv"

# 地点と判定温度の設定
LOCATION = "東京（トウキョウ）"
JUDGEMENT_TEMP = 27.0


def is_target_day() -> bool:
    """6月〜10月かつ金曜日かどうかを判定"""
    today = datetime.now()
    return 6 <= today.month <= 10 and today.weekday() == 4


def fetch_temperature_data(url: str) -> pd.DataFrame:
    """気象庁CSVをDataFrameで取得"""
    response = requests.get(url)
    response.encoding = "shift_jis"
    return pd.read_csv(StringIO(response.text))


def extract_temperature_info(df: pd.DataFrame, location: str) -> tuple[float, str]:
    """指定地点の最高気温と観測時刻を抽出"""
    row = df[df["地点"] == location]
    if row.empty:
        raise ValueError(f"{location} のデータが見つかりません")

    # 日付取得
    year = row["現在時刻(年)"].values[0]
    month = row["現在時刻(月)"].values[0]
    day = row["現在時刻(日)"].values[0]
    hour = row["現在時刻(時)"].values[0]
    minute = row["現在時刻(分)"].values[0]

    # 気温取得
    temp_column = f"{day}日の最高気温(℃)"
    if temp_column not in row.columns:
        raise KeyError(f"{temp_column} がCSVに存在しません")
    temperature = row[temp_column].values[0]

    # 観測時刻文字列
    timing = f"{year}年{month}月{day}日{hour}時{minute}分 計測"
    return temperature, timing


def generate_comment(temp: float) -> str:
    """気温に応じたメッセージ"""
    if temp > 30:
        return "本日は在宅作業よ。屋内でも熱中症になることも多いから、気を付けて。"
    elif temp > JUDGEMENT_TEMP:
        return "ハァ……暑すぎ。今日は在宅作業をオススメするけど。"
    else:
        return "本日は出社日よ。水分をこまめに摂って、出社中の熱中症には十分気を付けて。"


def post_to_slack(message: str):
    """Slackにメッセージを送信"""
    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    if not slack_url:
        raise EnvironmentError("SLACK_WEBHOOK_URL が環境変数に設定されていません。")

    payload = {"text": message}
    response = requests.post(slack_url, json=payload, headers={"Content-Type": "application/json"})

    if response.status_code != 200:
        raise RuntimeError(f"Slack送信失敗: {response.status_code}\n{response.text}")


def main():
    if not is_target_day():
        print("今日は実行対象日ではありません。終了します。")
        sys.exit(0)

    try:
        df = fetch_temperature_data(JMA_URL)
        temperature, timing = extract_temperature_info(df, LOCATION)
        comment = generate_comment(temperature)
        message = f"おはようございます\n{comment}\n\n{temperature}度@{timing}"
        print(message)
        post_to_slack(message)

    except Exception as e:
        print(f"[エラー] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
