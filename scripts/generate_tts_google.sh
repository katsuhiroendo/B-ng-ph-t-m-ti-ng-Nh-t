#!/bin/bash
# Google Cloud Text-to-Speech で、ひらがな表の音声（単音・単語）を一括生成します。
# macOS 標準の curl / plutil / base64 / zip だけで動きます。
#
# 使い方（ターミナルで）:
#   export GOOGLE_TTS_API_KEY='あなたのAPIキー'
#   bash generate_tts_google.sh            # 生成して ai-tts.zip を作る
#   bash generate_tts_google.sh --voices   # 使える日本語の声の一覧を表示
#   VOICE=ja-JP-Chirp3-HD-Charon bash generate_tts_google.sh   # 声を変える
set -u
VOICE="${VOICE:-ja-JP-Chirp3-HD-Aoede}"
RATE="${RATE:-0.9}"
API="https://texttospeech.googleapis.com/v1"
KEY="${GOOGLE_TTS_API_KEY:-}"
if [ -z "$KEY" ]; then
  echo "エラー: APIキーが設定されていません。先に次を実行してください:"
  echo "  export GOOGLE_TTS_API_KEY='あなたのAPIキー'"
  exit 1
fi

json_get() {  # json_get <file> <key>  → 値を標準出力へ
  if command -v plutil >/dev/null 2>&1; then
    plutil -extract "$2" raw -o - "$1" 2>/dev/null
  else
    python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));k=sys.argv[2].split(".");[d:=d[x] for x in k];print(d)' "$1" "$2" 2>/dev/null
  fi
}
b64dec() { base64 -D 2>/dev/null || base64 -d; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [ "${1:-}" = "--voices" ]; then
  curl -sS -H "X-Goog-Api-Key: $KEY" "$API/voices?languageCode=ja-JP" -o "$TMP/v.json"
  grep -o '"name": *"[^"]*"' "$TMP/v.json" | sed 's/.*"\(ja-JP[^"]*\)"/\1/' | sort
  exit 0
fi

OUT="ai-tts"
mkdir -p "$OUT"
echo "声: $VOICE  速さ: $RATE"
ok=0; ng=0; n=0
while IFS=$'\t' read -r id text; do
  [ -z "$id" ] && continue
  n=$((n+1))
  body="{\"input\":{\"text\":\"$text\"},\"voice\":{\"languageCode\":\"ja-JP\",\"name\":\"$VOICE\"},\"audioConfig\":{\"audioEncoding\":\"LINEAR16\",\"sampleRateHertz\":48000,\"speakingRate\":$RATE}}"
  code=$(curl -sS -o "$TMP/r.json" -w '%{http_code}' -X POST \
    -H "X-Goog-Api-Key: $KEY" -H "Content-Type: application/json; charset=utf-8" \
    --data "$body" "$API/text:synthesize")
  if [ "$code" = "200" ]; then
    json_get "$TMP/r.json" audioContent | b64dec > "$OUT/$id.wav"
    if [ -s "$OUT/$id.wav" ]; then ok=$((ok+1)); printf '\r%3d 件目 %-12s OK   ' "$n" "$id"; else ng=$((ng+1)); echo; echo "失敗: $id（音声データが空）"; fi
  else
    ng=$((ng+1)); echo
    echo "失敗: $id（HTTP $code）: $(json_get "$TMP/r.json" error.message)"
    if [ "$code" = "400" ] || [ "$code" = "403" ] || [ "$code" = "401" ]; then
      echo "→ APIキー、Text-to-Speech API の有効化、請求先アカウントの設定、声の名前（--voices で確認）を見直してください。"
      exit 1
    fi
  fi
done <<'LIST'
a	あ
i	い
u	う
e	え
o	お
ka	か
ki	き
ku	く
ke	け
ko	こ
sa	さ
shi	し
su	す
se	せ
so	そ
ta	た
chi	ち
tsu	つ
te	て
to	と
na	な
ni	に
nu	ぬ
ne	ね
no	の
ha	は
hi	ひ
fu	ふ
he	へ
ho	ほ
ma	ま
mi	み
mu	む
me	め
mo	も
ya	や
yu	ゆ
yo	よ
ra	ら
ri	り
ru	る
re	れ
ro	ろ
wa	わ
n	ん
ga	が
gi	ぎ
gu	ぐ
ge	げ
go	ご
za	ざ
ji	じ
zu	ず
ze	ぜ
zo	ぞ
da	だ
de	で
do	ど
ba	ば
bi	び
bu	ぶ
be	べ
bo	ぼ
pa	ぱ
pi	ぴ
pu	ぷ
pe	ぺ
po	ぽ
kya	きゃ
kyu	きゅ
kyo	きょ
sha	しゃ
shu	しゅ
sho	しょ
cha	ちゃ
chu	ちゅ
cho	ちょ
nya	にゃ
nyu	にゅ
nyo	にょ
hya	ひゃ
hyu	ひゅ
hyo	ひょ
mya	みゃ
myu	みゅ
myo	みょ
rya	りゃ
ryu	りゅ
ryo	りょ
gya	ぎゃ
gyu	ぎゅ
gyo	ぎょ
ja	じゃ
ju	じゅ
jo	じょ
bya	びゃ
byu	びゅ
byo	びょ
pya	ぴゃ
pyu	ぴゅ
pyo	ぴょ
wi	ウィ
we	ウェ
wo	ウォ
ye	イェ
va	ヴァ
vi	ヴィ
vu	ヴ
ve	ヴェ
vo	ヴォ
she	シェ
je	ジェ
che	チェ
tsa	ツァ
tsi	ツィ
tse	ツェ
tso	ツォ
ti	ティ
tu	トゥ
di	ディ
du	ドゥ
tyu	テュ
dyu	デュ
fa	ファ
fi	フィ
fe	フェ
fo	フォ
fyu	フュ
w-kitte	きって
w-gakkou	がっこう
w-kippu	きっぷ
w-okaasan	おかあさん
w-oniisan	おにいさん
w-kuuki	くうき
w-sensei	せんせい
w-otousan	おとうさん
w-watashiwa	わたしは
w-konnichiwa	こんにちは
w-gakkoue	がっこうへ
w-hon-o-yomimasu	ほんを よみます
w-mizu-o-nomimasu	みずを のみます
w-shinbun	しんぶん
w-ringo	りんご
w-beddo	ベッド
w-kappu	カップ
w-sakkaa	サッカー
w-koohii	コーヒー
w-keeki	ケーキ
w-nooto	ノート
w-suupaa	スーパー
w-pan	パン
w-pen	ペン
w-wain	ワイン
w-fooku	フォーク
w-paatii	パーティー
w-chekku	チェック
w-fairu	ファイル
w-vaiorin	ヴァイオリン
LIST
echo
printf 'voice=%s\nrate=%s\ndate=%s\n' "$VOICE" "$RATE" "$(date '+%Y-%m-%d %H:%M')" > "$OUT/_info.txt"
rm -f ai-tts.zip
(cd "$OUT" && zip -q -r ../ai-tts.zip .)
echo "完了: 成功 $ok 件 / 失敗 $ng 件"
echo "→ できた ai-tts.zip を Claude との会話に添付してください。"
