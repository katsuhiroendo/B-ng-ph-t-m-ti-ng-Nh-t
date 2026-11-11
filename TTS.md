# AI音声（Google Cloud Text-to-Speech）の作り方

学習者の端末に関係なく、全員が同じ高品質の合成音声で聞けるようにするため、Google のAI音声で音声ファイルを事前に作成します。
ページの「Giọng đọc」で「Giọng AI chất lượng cao (Google)」を選ぶと、このファイルが再生されます。

- 声：`ja-JP-Chirp3-HD-Aoede`（女性）。Google の最上位の音声（Chirp 3 HD）
- 対象：単音128件＋単語30件＝158件（約400文字）。行の連続読みは単音をつないで再生します
- 費用：Chirp 3 HD は月100万文字まで無料のため、0円です

## 1. Google Cloud の準備（初回のみ・約10分）

1. https://console.cloud.google.com/ に Google アカウントでログインし、新しいプロジェクトを作成します（例：`kana-tts`）。
2. 「お支払い」で請求先アカウントを設定します。無料枠の範囲でも、クレジットカードの登録が必要です。
3. Text-to-Speech API を有効にします：https://console.cloud.google.com/apis/library/texttospeech.googleapis.com →「有効にする」
4. 「APIとサービス」→「認証情報」→「認証情報を作成」→「APIキー」を選びます。
5. 作成したキーの「キーを制限」を開き、「APIの制限」で「Cloud Text-to-Speech API」だけを選んで保存します（キーが漏れたときの被害を限定するためです）。

任意：「お支払い」→「予算とアラート」で、予算を100円程度に設定しておくと安心です。

## 2. 音声を生成する（約2分）

`scripts/generate_tts_google.sh` をダウンロードし（例：ダウンロードフォルダ）、ターミナルで実行します。

```
cd ~/Downloads
export GOOGLE_TTS_API_KEY='ここにAPIキー'
bash generate_tts_google.sh --voices    # 日本語の声の一覧（任意）
bash generate_tts_google.sh
```

完了すると、同じフォルダに `ai-tts.zip` ができます。Claude との会話に添付してください。

- 声を変える場合：`VOICE=ja-JP-Chirp3-HD-Charon bash generate_tts_google.sh`（男性の例）
- 速さを変える場合：`RATE=1.0 bash generate_tts_google.sh`（初期値は0.9）
- APIキーは会話に貼らないでください。

## 3. 公開用に加工する

```
python3 scripts/process_audio.py --ai ai-tts.zip
```

無音カット・音量の統一・mp3化を行い、`audio/ai/` に出力します。録音（`audio/`）は変更しません。
