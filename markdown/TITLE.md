\newpage

# まえがき {-}

## このドキュメントは何 {-}

この本は、「勝手にアプリケーションノート4」で設計製作したリレーマトリクスHATを応用し、既存のSCPIデバイス"U2751A"をエミュレートするまでを解説
したドキュメントです。SCPIのふりをする部分はラズピコ(Raspberry Pi pico)が行います。ラズピコの開発はMicroPythonとPyCharmで行いました。
ラズピコにこだわりはなく、USBシリアルコンバータと任意のUART持ちマイコンで実現可能だと思います。

ここ2年ほどの半導体供給不安のせいで計測器類（すなわちSCPIデバイス）が入手難になったことがこの思いつきのきっかけです
(KeysightのU2751Aスイッチマトリクスを仕事で購入しましたが、納期が3ヶ月かかりました)。この機械と同様の機能をもち、なおかつ自作可能な
入手性のよい装置が欲しくなったので、「なければ作る」の精神で作りました。

エミュレートとは言っても、SCPI・IEEE488の厳密な準拠はしていません。たとえばセミコロンで数珠つなぎする部分などの実装はバッサリカットしましたし、
エラーハンドリングもけっこう適当です。

この本の構成は大きく３部構成です。エミュレーション方針の説明と処理フローの説明、そして関連するMicroPythonライブラリ全文を載せました。
ライブラリの内容については、印刷後に更新される可能性が十分にあるので、参考にとどめてください。

## GreenPAKは死んだ！なぜだ！（Rだからさ） {-}

2022年8月、非常に残念なことに、GreenPakの石を作っていたDialog社はルネサスに吸収されてしまいました。
この本が出される2022年12月31日がD社が登記上？存在する最後の日です。少なくとも日本では。

**Silego/Dialog時代にあった直販サイトはもうありません。**
Mouserではかろうじて一部の石を売っています。おそらくマクニカがRの代理店だからでしょう。DigiKeyでは納期が全部５２週になっています。
Mouserにしても、GreenPAKから派生した**ForgeFPGAの開発キットを買えなくした**あたりからすると、もう先はないのかもしれません。
このキット、筆者の記憶が正しければ、2022年８月に新商品として購入可能になったばかりでした。同年１１月に購入不能になりました。

- <https://www.mouser.jp/ProductDetail/Dialog-Semiconductor/SLG7DVKFORGE?qs=Rp5uXu7WBW9lupzVV%252Bp7VQ%3D%3D>

そういうとこやぞ&#174;

\toc

# SCPIエミュレーション方針

エミュレーション対象の機能が比較的単純なこともあり、実装も簡易なものにしました。IEEE488の共通コマンド応答の実装もしょぼめです。
本来は互換性についての定義もあるはずですが、調査しきれていません。SCPI-1999のドキュメントPDFを見つけたので参考に置いておきます。

- <https://www.keysight.com/us/en/assets/9921-01870/miscellaneous/SCPI-99.pdf>

## 割り切り

上のとおり、**SCPIの完全な実装は目指さない**方針で行きます。例えばセミコロンでつないでも最初の項だけ解釈する、ステータスレジスタを持たないなどです。
[@tbl:ieee488-commands]に共通コマンドの実装ステータス一覧を示します。いまのところ`*IDN?`には応答を返します。

::: {.table width=[0.5,0.5]}
Table: IEEE488コマンド実装ステータス {#tbl:ieee488-commands}

|          SCPI | Implemented  |
|--------------:|:-------------|
|        `*CLS` |              |
|  `*ESE/*ESE?` |              |
|       `*ESR?` |              |
|       `*IDN?` | &check;      |
|  `*OPC/*OPC?` |              |
|        `*RST` |              |
|  `*SRE/*SRE?` |              |
|       `*STB?` |              |
|       `*TST?` |              |

:::

# スイッチマトリクス「Keysight/Agilent U2751A」

今回モデルにしたKeysight(Agilent)社の計測器「U2751A」について簡単に説明します。USBモジュラーデータ収集装置シリーズの一つで、単体で使えるだけでなく、
他のモジュールとともに最大6台、シャーシに収めて使うことができます。Keysightが提供している専用ソフトからスイッチを操作できる他、
SCPIコマンドでの操作も受け付けます。専用ソフト一式をインストールしたPCあればNI VISA環境でも操作できます。関連リンクを以下に示します。

- <https://www.keysight.com/us/en/products/modular/data-acquisition-daq/usb-modular-data-acquisition.html>
- <https://www.keysight.com/us/en/product/U2751A/4x8-2-wire-usb-modular-switch-matrix.html>

## コマンド一覧

::: {.table width=[0.4,0.4,0.2]}
Table: U2751A固有SCPIコマンド実装ステータス {#tbl:u2751a-commands}

| SCPI                            | Parameter             | Implemented |
|---------------------------------|-----------------------|:------------|
| `DIAGnostic:RELay:CYCLes?`      | None                  |             |
| `DIAGnostic:RELay:CYCLes:CLEar` | None                  |             |
| `ROUTe:CLOSe`                   | `(@101,102:105,201:)` | &check;     |
| `ROUTe:CLOSe?`                  | `(@101,102:105,201:)` | &check;     |
| `ROUTe:OPEN`                    | `(@101,102:105,201:)` | &check;     |
| `ROUTe:OPEN?`                   | `(@101,102:105,201:)` | &check;     |
| `SYSTem:CDEScription?`          | None                  |             |
| `SYSTem:ERRor?`                 | None                  |             |
| `SYSTem:VERSion?`               | None                  | &check;     |

:::

# アルゴリズムというか処理フロー

SCPIコマンドを受け取ったあとの処理はだいたい以下のような感じです。例として、ホストから`ROUTe:CLOSe (@101:103)<CR><LF>`が送られてきた場合の
処理を説明します。

#### １．標準入力で1行取り込んだあとセミコロンで区切り、最初の要素だけをパース処理に回す (main.py) {-}

[](micropython/main.py){.listingtable nocaption=true from=22 #lst:readline-parse .python}

ファイルの先頭で`gets = sys.stdin.readline`としてエイリアスを宣言しておいて、無限ループ内の`line = gets().strip()`で
標準入力から1行取り込んだのち空白文字を切り落とします。`line`の文字列長が0より大きければパース処理に回します。

- `line = "ROUTe:CLOSe (@101:103)"`

#### ２．パラメータ付きコマンドのことを考慮して空白とコロンで切り分ける（MicroScpiDevice.py） {-}

[](micropython/MicroScpiDevice.py){.listingtable nocaption=true from=48 to=65 #lst:split-command-parameter .python}

U2751Aではわずか2種類ですが、一部コマンドはパラメータを受けることができます。コマンドとパラメータは空白で区分けされます。
`mini_lexer()`がこの部分の処理を行います。最初の空白の直前までをコマンド文字列、残り全部をパラメータ文字列と考えます。
さらに、コマンド文字列はコロンで区切られている場合があるので、`split(":")`で文字列のリストに変換します。
`mini_lexer()`はこれらをタプルにして返却します。

- `candidate_cmd = ["ROUTe", "CLOSe"]`
- `candidate_param = "(@101:103)"`

#### ３．要素数が合致するコマンドに候補を絞り込む（MicroScpiDevice.py） {-}

[](micropython/MicroScpiDevice.py){.listingtable nocaption=true from=74 to=78 #lst:get-command-candidate .python}

`mini_lexer()`に返されたコマンド文字列のリストの要素数と一致する登録済コマンドを抽出します。コマンドがクエリかどうかは
リストの最後の要素が"?"で終わっているかどうかで判定します。
登録済コマンドの中に長さが等しいものが一つもない場合はエラーになります。

今回は長さ２であるコマンドが抽出されます。

``` .python
length_matched = [
    ScpiCommand(keywords=(ScpiKeyword(long='ROUTe', short='ROUT'), ScpiKeyword(long='CLOSe', short='CLOS')),
                query=False, callback= < bound_method >),
    ScpiCommand(keywords=(ScpiKeyword(long='ROUTe', short='ROUT'), ScpiKeyword(long='OPEN', short='OPEN')),
                query=False, callback= < bound_method >)
]
```

#### ４．すべてのコマンド文字列が一致した場合はコールバック関数を呼び出す（MicroScpiDevice.py） {-}

`length_matched`の各`ScpiCommand`アイテムについて`keywords`に登録された`ScpiKeyword`の全てにマッチするかを調べます。
全てにマッチする最初の`ScpiCommand`アイテムに登録されたコールバック関数を呼び出します。一つもマッチがない場合はエラーになります。
コールバック関数は引数にパラメタ文字列とクエリフラグを受け取ります。

[](micropython/MicroScpiDevice.py){.listingtable nocaption=true from=80 #lst:callback-when-all-matched .python}

#### コールバック関数内でパラメタ文字列のパースやクエリに返答するなどを含む最終的な処理をする（EMU2751A.py） {-}

# GpakMuxモジュール

スイッチマトリクスHATを操作するためのモジュールです。前回ラズパイ用に書いたものを移植・改変しました。スイッチマトリクスの接続状態を返す`query()`
と数値から行・列の情報を返す`int_to_rowcol()`が足されています。
もっとうまい設計できそうだけど動くからヨシ！ってことで。

[GpakMuxモジュール](micropython/GpakMux.py){.listingtable .python from=86 to=156 #lst:gpakmux-module}

# MicroScpiDeviceモジュール

MicroScpiDeviceモジュールは今作の肝となる「マイクロSCPIデバイス」の挙動を定義したものです。
キーワードおよびコマンド定義のためのヘルパークラス（`ScpiKeyword`、`ScpiCommand`）と、SCPIデバイスの共通動作を定義した`MicroScpiDevice`
クラスの3部構成です。

## ScpiKeywordクラス

SCPIコマンドを構成するキーワードの定義クラスです。候補文字列を検証してキーワード定義に一致すると`True`を返すクラス関数`match()`を持っています。
引数`long`と`short`はそれぞれ完全表記（long form）と短縮表記（short form）に当たります。
これらの定義が動作中に変わることはないので、`namedtuple`を継承しています。

`match()`はこれら2つだけでなく、中間の表記も認めています。 たとえば`kw = ScpiKeyword(long="DEFault", short="DEF")`のとき、
`DEF`/`DEFA`/`DEFAU`/`DEFAUL`/`DEFAULT`の全てにマッチしますが、`DEFINE`にはマッチしません。
関数内部で大文字に変換しているので、候補文字列の大文字小文字を区別しません。

[ScpiKeywordクラス](micropython/MicroScpiDevice.py){.listingtable .python from=8 to=30 #lst:scpikeyword-class}

## ScpiCommandクラス

SCPIコマンドの定義クラスです。`ScpiKeyword`のタプルとクエリコマンドを表すフラグ、マッチしたときのコールバック関数へのポインタを登録します。

[ScpiCommandクラス](micropython/MicroScpiDevice.py){.listingtable .python from=33 to=39 #lst:scpicommand-class}

## MicroScpiDeviceクラス

SCPIデバイスの定義クラスです。`mini_lexer()`がコマンド文字列の分解処理、`parse_and_process()`がコマンドの走査とコールバック 関数の
呼び出しを行います。

[MicroScpiDeviceクラス](micropython/MicroScpiDevice.py){.listingtable .python from=44 to=94 #lst:microscpidevice-class}

# EMU2751Aモジュール

## CrossBarsクラス

スイッチマトリクスの接点データ管理クラスです。

[CrossBarsクラス](micropython/EMU2751A.py){.listingtable .python from=33 to=76 #lst:crossbars-class}

## EMU2751Aクラス

[EMU2751Aクラス](micropython/EMU2751A.py){.listingtable .python from=78 #lst:emu2751a-class}

# #include "extra_libs.md"

# あとがき {-}

- タルコフのワイプ・パッチ１３に間に合うように頑張って書きました。今回も前日印刷&trade;です（１２月２８日）
- 本当はForgeFPGA試食本も書きたかったけどこっちの筆が進まんくて間に合わんかったすまん
- ライブラリの設計はラズピコのメモリ量に頼っている部分があるので、ほかのMicroPythonなマイコンに移植できるかはやってみないとわかりません
