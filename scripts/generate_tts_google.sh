#!/bin/bash
# Google Cloud Text-to-Speech で、ひらがな表の音声（単音・単語）を一括生成します。
# macOS 標準の curl / plutil / base64 / zip だけで動きます。
#
# 使い方（ターミナルで）:
#   export GOOGLE_TTS_API_KEY='あなたのAPIキー'
#   bash generate_tts_google.sh            # 全158件を生成して ai-tts.zip を作る
#   bash generate_tts_google.sh --test     # 問題のあった音を2方式で試作して ai-tts-test.zip を作る
#   bash generate_tts_google.sh --voices   # 使える日本語の声の一覧
# 設定（環境変数）:
#   VOICE=ja-JP-Chirp3-HD-Aoede  声     RATE=0.9  速さ
#   KANA=hira|kata  単音を読ませる文字   FRAME=ssml|plain  単音の前後に無音を入れるか
set -u
VOICE="${VOICE:-ja-JP-Chirp3-HD-Aoede}"
RATE="${RATE:-0.9}"
KANA="${KANA:-hira}"
FRAME="${FRAME:-ssml}"
API="https://texttospeech.googleapis.com/v1"
KEY="${GOOGLE_TTS_API_KEY:-}"
if [ -z "$KEY" ]; then
  echo "エラー: APIキーが設定されていません。先に次を実行してください:"
  echo "  export GOOGLE_TTS_API_KEY='あなたのAPIキー'"
  exit 1
fi

json_get() {
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

cat > "$TMP/list.tsv" <<'LIST'
a	あ	ア
i	い	イ
u	う	ウ
e	え	エ
o	お	オ
ka	か	カ
ki	き	キ
ku	く	ク
ke	け	ケ
ko	こ	コ
sa	さ	サ
shi	し	シ
su	す	ス
se	せ	セ
so	そ	ソ
ta	た	タ
chi	ち	チ
tsu	つ	ツ
te	て	テ
to	と	ト
na	な	ナ
ni	に	ニ
nu	ぬ	ヌ
ne	ね	ネ
no	の	ノ
ha	は	ハ
hi	ひ	ヒ
fu	ふ	フ
he	へ	ヘ
ho	ほ	ホ
ma	ま	マ
mi	み	ミ
mu	む	ム
me	め	メ
mo	も	モ
ya	や	ヤ
yu	ゆ	ユ
yo	よ	ヨ
ra	ら	ラ
ri	り	リ
ru	る	ル
re	れ	レ
ro	ろ	ロ
wa	わ	ワ
n	ん	ン
ga	が	ガ
gi	ぎ	ギ
gu	ぐ	グ
ge	げ	ゲ
go	ご	ゴ
za	ざ	ザ
ji	じ	ジ
zu	ず	ズ
ze	ぜ	ゼ
zo	ぞ	ゾ
da	だ	ダ
de	で	デ
do	ど	ド
ba	ば	バ
bi	び	ビ
bu	ぶ	ブ
be	べ	ベ
bo	ぼ	ボ
pa	ぱ	パ
pi	ぴ	ピ
pu	ぷ	プ
pe	ぺ	ペ
po	ぽ	ポ
kya	きゃ	キャ
kyu	きゅ	キュ
kyo	きょ	キョ
sha	しゃ	シャ
shu	しゅ	シュ
sho	しょ	ショ
cha	ちゃ	チャ
chu	ちゅ	チュ
cho	ちょ	チョ
nya	にゃ	ニャ
nyu	にゅ	ニュ
nyo	にょ	ニョ
hya	ひゃ	ヒャ
hyu	ひゅ	ヒュ
hyo	ひょ	ヒョ
mya	みゃ	ミャ
myu	みゅ	ミュ
myo	みょ	ミョ
rya	りゃ	リャ
ryu	りゅ	リュ
ryo	りょ	リョ
gya	ぎゃ	ギャ
gyu	ぎゅ	ギュ
gyo	ぎょ	ギョ
ja	じゃ	ジャ
ju	じゅ	ジュ
jo	じょ	ジョ
bya	びゃ	ビャ
byu	びゅ	ビュ
byo	びょ	ビョ
pya	ぴゃ	ピャ
pyu	ぴゅ	ピュ
pyo	ぴょ	ピョ
wi	ウィ	ウィ
we	ウェ	ウェ
wo	ウォ	ウォ
ye	イェ	イェ
va	ヴァ	ヴァ
vi	ヴィ	ヴィ
vu	ヴ	ヴ
ve	ヴェ	ヴェ
vo	ヴォ	ヴォ
she	シェ	シェ
je	ジェ	ジェ
che	チェ	チェ
tsa	ツァ	ツァ
tsi	ツィ	ツィ
tse	ツェ	ツェ
tso	ツォ	ツォ
ti	ティ	ティ
tu	トゥ	トゥ
di	ディ	ディ
du	ドゥ	ドゥ
tyu	テュ	テュ
dyu	デュ	デュ
fa	ファ	ファ
fi	フィ	フィ
fe	フェ	フェ
fo	フォ	フォ
fyu	フュ	フュ
w-kitte	きって	キッテ
w-gakkou	がっこう	ガッコウ
w-kippu	きっぷ	キップ
w-okaasan	おかあさん	オカアサン
w-oniisan	おにいさん	オニイサン
w-kuuki	くうき	クウキ
w-sensei	せんせい	センセイ
w-otousan	おとうさん	オトウサン
w-watashiwa	わたしは	ワタシハ
w-konnichiwa	こんにちは	コンニチハ
w-gakkoue	がっこうへ	ガッコウヘ
w-hon-o-yomimasu	ほんを よみます	ホンヲ ヨミマス
w-mizu-o-nomimasu	みずを のみます	ミズヲ ノミマス
w-shinbun	しんぶん	シンブン
w-ringo	りんご	リンゴ
w-beddo	ベッド	ベッド
w-kappu	カップ	カップ
w-sakkaa	サッカー	サッカー
w-koohii	コーヒー	コーヒー
w-keeki	ケーキ	ケーキ
w-nooto	ノート	ノート
w-suupaa	スーパー	スーパー
w-pan	パン	パン
w-pen	ペン	ペン
w-wain	ワイン	ワイン
w-fooku	フォーク	フォーク
w-paatii	パーティー	パーティー
w-chekku	チェック	チェック
w-fairu	ファイル	ファイル
w-vaiorin	ヴァイオリン	ヴァイオリン
LIST

synth() {  # synth <id> <text> <kana> <frame> <outfile>
  local id="$1" text="$2" kana="$3" frame="$4" out="$5" t input
  t="$text"
  case "$id" in w-*) frame=plain ;; *) [ "$kana" = "kata" ] && t="$6" ;; esac
  if [ "$frame" = "ssml" ]; then
    input="{\"ssml\":\"<speak><break time=\\\"400ms\\\"/>$t<break time=\\\"400ms\\\"/></speak>\"}"
  else
    input="{\"text\":\"$t\"}"
  fi
  body="{\"input\":$input,\"voice\":{\"languageCode\":\"ja-JP\",\"name\":\"$VOICE\"},\"audioConfig\":{\"audioEncoding\":\"LINEAR16\",\"sampleRateHertz\":48000,\"speakingRate\":$RATE}}"
  code=$(curl -sS -o "$TMP/r.json" -w '%{http_code}' -X POST \
    -H "X-Goog-Api-Key: $KEY" -H "Content-Type: application/json; charset=utf-8" \
    --data "$body" "$API/text:synthesize")
  if [ "$code" = "200" ]; then
    json_get "$TMP/r.json" audioContent | b64dec > "$out"
    [ -s "$out" ] && return 0
    echo; echo "失敗: $id（音声データが空）"; return 1
  fi
  echo; echo "失敗: $id（HTTP $code）: $(json_get "$TMP/r.json" error.message)"
  case "$code" in 400|401|403)
    echo "→ APIキー、Text-to-Speech API の有効化、請求先アカウントの設定、声の名前（--voices で確認）を見直してください。"
    exit 1 ;;
  esac
  return 1
}

ok=0; ng=0; n=0
if [ "${1:-}" = "--test" ]; then
  OUT="ai-tts-test"; ZIP="ai-tts-test.zip"
  SUSPECT=" i chi da e gu ki mi n ni nu mo to ze kyo tu ti cho ru su bya ka sa a "
  rm -rf "$OUT"; mkdir -p "$OUT"
  while IFS=$'\t' read -r id text ktext; do
    case "$SUSPECT" in *" $id "*) ;; *) continue ;; esac
    for v in "hira ssml h" "kata ssml k" "hira plain p"; do
      set -- $v; n=$((n+1))
      if synth "$id" "$text" "$1" "$2" "$OUT/${id}__$3.wav" "$ktext"; then ok=$((ok+1)); printf '\r%3d 件 %-10s OK   ' "$n" "$id"; else ng=$((ng+1)); fi
    done
  done < "$TMP/list.tsv"
else
  OUT="ai-tts"; ZIP="ai-tts.zip"
  rm -rf "$OUT"; mkdir -p "$OUT"
  echo "声: $VOICE  速さ: $RATE  文字: $KANA  前後の無音: $FRAME"
  while IFS=$'\t' read -r id text ktext; do
    [ -z "$id" ] && continue
    n=$((n+1))
    if synth "$id" "$text" "$KANA" "$FRAME" "$OUT/$id.wav" "$ktext"; then ok=$((ok+1)); printf '\r%3d 件目 %-18s OK   ' "$n" "$id"; else ng=$((ng+1)); fi
  done < "$TMP/list.tsv"
fi
echo
printf 'voice=%s\nrate=%s\nkana=%s\nframe=%s\ndate=%s\n' "$VOICE" "$RATE" "$KANA" "$FRAME" "$(date '+%Y-%m-%d %H:%M')" > "$OUT/_info.txt"
rm -f "$ZIP"
(cd "$OUT" && zip -q -r "../$ZIP" .)
echo "完了: 成功 $ok 件 / 失敗 $ng 件"
echo "→ できた $ZIP を Claude との会話に添付してください。"
