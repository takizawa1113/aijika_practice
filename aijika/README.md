# 空いてる時間、どうする？ — ファイル構成

元の `app.py` 1ファイル（約880行）を、役割ごとに分割しました。
`app.py` はルーティングだけを行う薄いファイルになっています。

## ファイル構成

```
project/
├── app.py                      # エントリーポイント（初期化・画面ディスパッチのみ）
├── config.py                   # 定数（DBパス、メニュー構成、選択肢など）
├── styles.py                   # 共通CSS
├── database.py                 # DB接続・スキーマ定義・サンプルデータ投入
├── employee_repository.py      # employees テーブルのアクセス
├── request_repository.py       # support_requests テーブルのアクセス
├── free_time_repository.py     # free_times テーブルのアクセス
├── application_repository.py   # applications テーブルのアクセス
├── matching.py                 # マッチングスコア計算・おすすめ抽出ロジック
├── sidebar.py                  # サイドバーメニューの描画・画面遷移
├── google_calendar_service.py  # Googleカレンダー連携（ダミーデータ版）
├── outlook_calendar_service.py # Outlook連携（本物のMicrosoft Graph版）
├── calendar_utils.py           # 「予定→空き時間」計算ロジック（両連携先で共通）
├── views/
│   ├── home.py                 # ホーム画面
│   ├── search.py                # 支援を探す画面
│   ├── request_form.py         # 支援を依頼する画面
│   ├── free_time_form.py       # 余白時間を登録画面
│   ├── calendar_view.py        # カレンダー画面
│   ├── mypage.py                # マイページ画面
│   └── notices.py               # お知らせ画面
├── .streamlit/
│   └── secrets.toml.example    # Outlook連携用クライアントIDのテンプレート
├── .gitignore                  # secrets.toml・token_cache等をコミットしないため
├── requirements.txt
└── resource_matching.db
```

## 設計の考え方

- **app.py は「画面を1個選んで呼ぶだけ」にする。** 各画面の中身をここに書かない。
- **DBアクセスはテーブル単位で分ける**（`*_repository.py`）。検索機能を触る人と
  余白時間登録を触る人が同時に作業しても、別ファイルなのでコンフリクトしにくい。
- **マッチングロジック（`matching.py`）は DB や Streamlit に依存しない純粋な関数**
  にしてある。`requests_df` のような DataFrame を引数として受け取るだけなので、
  ロジックの調整をする人がいても画面側の変更と衝突しにくく、将来的に
  `pytest` で単体テストも書きやすい。
- **画面（views/）は「1画面＝1ファイル」。** 新しい画面を増やすときは
  `views/` にファイルを追加し、`config.PAGES` と `app.py` の
  `PAGE_RENDERERS` にそれぞれ1行足すだけでよい。

## 3人チームでの分担例

作業がぶつかりにくいよう、機能のまとまりで担当を分けるのがおすすめです。
「基盤・マッチング」はアプリで一番複雑な部分がまとまっているため、
`views/home.py` など比較的独立して触れる画面は他のメンバーに寄せて、
3人の作業量が偏りすぎないようにしています。

- **Aさん（班長・基盤＆マッチング）**: `matching.py`, `database.py`,
  `config.py`, `styles.py`, `sidebar.py`, `app.py`
- **Bさん（検索・依頼＋ホーム）**: `views/search.py`, `views/request_form.py`,
  `request_repository.py`, `views/home.py`, `views/notices.py`
- **Cさん（余白時間・カレンダー・マイページ）**: `views/free_time_form.py`,
  `views/calendar_view.py`, `views/mypage.py`, `free_time_repository.py`,
  `application_repository.py`, `employee_repository.py`,
  `google_calendar_service.py`

`config.py` と `app.py` は全員が触る可能性がある「共有地」なので、
メニューを増やす・定数を変えるといった変更は小さくまとめてこまめに
コミット／プルするとコンフリクトを避けやすくなります。

## 元コードから直した点（レビューで見つかったバグ）

分割の過程で、元の `app.py` にあった以下の不具合も修正しています。

1. **ホーム画面のボタンでページ遷移しない問題**
   元コードは `st.session_state.selected_page` にページ名をセットして
   `st.rerun()` していましたが、サイドバーの `st.radio` がその値を
   参照していなかったため、実際にはメニューが切り替わりませんでした。
   `sidebar.py` に `navigate_to()` を用意し、ボタン側からは
   `sidebar.navigate_to("余白時間を登録")` のように呼び出すことで、
   確実にメニューが切り替わるようにしています。

2. **「応募画面へ」ボタンがエラーになる問題**
   `st.form(...)` のブロック内で通常の `st.button()` を使っており、
   Streamlit の仕様上これは許可されていません
   （`st.form_submit_button()` 以外のボタンはフォーム内に置けない）。
   マッチング結果が1件でもあるデータで「余白時間を登録」を実行すると
   エラーになります。該当箇所をフォームの外側に移し、正常に動作する
   ようにしました。

いずれも動作確認用のテストスクリプトで全画面・主要な操作
（フォーム送信、ページ遷移ボタン）を実行し、例外が出ないことを確認済みです。

## カレンダー連携（Googleダミー版 ＋ Outlook本物版）

「余白時間を登録」画面に、カレンダーの予定を読み込んで空き時間を
提案する機能があります。画面上部の「連携先」で以下の2つを
その場で切り替えられます。

- **ダミーデータ（デモ用）**: `google_calendar_service.py`。
  実際のAPIは呼ばず、ランダムだが日付ごとに固定された架空の予定を
  生成して「動きだけ」を再現する。ネット環境やログインに依存しないので、
  常に動く安全策として残してある。
- **Outlook（本物・Microsoft Graph）**: `outlook_calendar_service.py`。
  MSAL（Microsoft Authentication Library）経由で個人のOutlook
  （outlook.com等）アカウントにログインし、実際にその日の予定を
  Microsoft Graph API から取得する。

どちらも `get_busy_events(date)` が
`[{"start": "HH:MM", "end": "HH:MM", "summary": str}, ...]`
という同じ形式で予定を返すので、`views/free_time_form.py` 側は
連携先を意識せずに同じコードで扱える。「予定から空き時間を計算する」
ロジックも `calendar_utils.py` に共通化してある。

- 日付を選ぶと、その日の予定が表示される
- 予定の合間から1時間以上の空き時間を自動計算し、候補ボタンとして表示
- 候補ボタンを押すと、下の登録フォームの日付・開始・終了時刻に自動反映される
- 取得に失敗した場合（未ログイン・設定不足など）はエラーメッセージを表示し、
  アプリ自体はクラッシュしない。発表中にうまくいかなければ「ダミーデータ」に
  切り替えれば続行できる。

### Outlook（本物）を使うための事前準備

**① Azure Portalでの作業（ご自身のMicrosoftアカウントで実施）**

1. https://portal.azure.com/ → 「Microsoft Entra ID」→「アプリの登録」→
   「新規登録」
2. 名前は任意
3. 「サポートされているアカウントの種類」で
   「個人の Microsoft アカウントのみ」を選択
4. 「リダイレクトURI」でプラットフォーム
   「パブリック クライアント/ネイティブ (モバイルとデスクトップ)」を選び、
   `http://localhost` を追加して登録
5. 登録後に表示される「アプリケーション (クライアント) ID」をコピー
6. 「APIのアクセス許可」→「Microsoft Graph」→「委任されたアクセス許可」→
   `Calendars.Read` を追加（個人アカウントなら管理者の承認は不要）

**② アプリ側の設定**

1. `pip install -r requirements.txt`（`msal`, `requests` を追加済み）
2. `.streamlit/secrets.toml.example` を `.streamlit/secrets.toml` に
   コピーし、①でコピーしたクライアントIDを貼り付ける
   （`secrets.toml` は `.gitignore` 済みなのでコミットされない）
3. `streamlit run app.py` → 「余白時間を登録」→ 連携先を
   「Outlook（本物）」に切り替えると、初回はブラウザが開いてログインを
   求められる。ログイン結果は `outlook_token_cache.bin` に保存され、
   2回目以降は自動的にログイン済みの状態になる
   （このファイルも `.gitignore` 済み）

デモ本番中に初めてログインすると不安定になりやすいので、**発表直前に
一度ログインを済ませておく**ことを強くおすすめします。終日の予定
（祝日など）は空き時間計算から自動的に除外されます。

## セットアップ

```bash
pip install -r requirements.txt
streamlit run app.py
```
