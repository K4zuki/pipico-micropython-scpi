\newpage

# まえがき {-}

## このドキュメントは何 {-}

この本は、「勝手にアプリケーションノート4」で設計製作したリレーマトリクスHATを応用し、既存のSCPIデバイス"U2751A"をエミュレートするまでを解説
したドキュメントです。SCPIのふりをする部分はラズピコ(Raspberry Pi pico)が行います。ラズピコの開発はMicroPythonとPyCharmで行いました。

ここ2年ほどの半導体供給不安のせいで計測器類（すなわちSCPIデバイス）が入手難になったことがこの思いつきのきっかけです
(Keysight/AgilentのU2751Aスイッチマトリクスを仕事で購入しましたが、納期が3ヶ月かかりました)。この機械と同様の機能をもち、なおかつ自作可能な
入手性のよい

エミュレートとは言っても、SCPI・IEEE488の厳密な準拠はしていません。たとえばセミコロンで数珠つなぎする部分などの実装はバッサリカットしましたし、
エラーハンドリングもけっこう適当です。

## GreenPAKは死んだ！なぜだ！（Rだからさ） {-}

2022年8月、非常に残念なことに、GreenPakの石を作っていたDialog社はルネサスに吸収されてしまいました。
**Silego/Dialog時代にあった直販サイトももうありません。**
Mouserではかろうじて一部の石を売っていますが、GreenPAKから派生した**ForgeFPGAの開発キットをディスコンにした**あたりからすると、もう先はないのかもしれません。
この本が出される2022年12月31日がD社が登記上？存在する最後の日です。少なくとも日本では。

そういうとこやぞ&#174;

\toc

# SCPIエミュレーション方針

エミュレーション対象の機能が比較的単純なこともあり、実装も簡易なものにしました。IEEE488の共通コマンド応答の実装もしょぼめです。
本来は互換性についての定義もあるはずですが、調査しきれていません。

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
SCPIコマンドでの操作も受け付けます。専用ソフト一式をインストールしたPCあればNI VISA環境でも操作できます。

- https://www.keysight.com/us/en/products/modular/data-acquisition-daq/usb-modular-data-acquisition.html
- https://www.keysight.com/us/en/product/U2751A/4x8-2-wire-usb-modular-switch-matrix.html

## コマンド一覧

::: {.table width=[0.4,0.4,0.2]}
Table: U2751A固有コマンド実装ステータス {#tbl:u2751a-commands}

| SCPI                            | Parameter             | Implemented  |
|---------------------------------|-----------------------|:-------------|
| `DIAGnostic:RELay:CYCLes?`      | None                  |              |
| `DIAGnostic:RELay:CYCLes:CLEar` | None                  |              |
| `ROUTe:CLOSe`                   | `(@101,102:105,201:)` | &check;      |
| `ROUTe:CLOSe?`                  | `(@101,102:105,201:)` | &check;      |
| `ROUTe:OPEN`                    | `(@101,102:105,201:)` | &check;      |
| `ROUTe:OPEN?`                   | `(@101,102:105,201:)` | &check;      |
| `SYSTem:CDEScription?`          | None                  |              |
| `SYSTem:ERRor?`                 | None                  |              |
| `SYSTem:VERSion?`               | None                  |              |

:::

# GpakMuxモジュール

[GpakMuxモジュール](micropython/GpakMux.py){.listingtable .python from=1 to=10 #lst:gpakmux-module}

# MicroScpiDeviceモジュール

## ScpiKeywordクラス

[ScpiKeywordクラス](micropython/MicroScpiDevice.py){.listingtable .python from=8 to=30 #lst:scpikeyword-class}

## ScpiCommandクラス

[ScpiCommandクラス](micropython/MicroScpiDevice.py){.listingtable .python from=33 to=39 #lst:scpicommand-class}

## MicroScpiDeviceクラス

[MicroScpiDeviceクラス](micropython/MicroScpiDevice.py){.listingtable .python from=44 to=94 #lst:microscpidevice-class}

# EMU2751Aモジュール

## CrossBarsクラス

[CrossBarsクラス](micropython/EMU2751A.py){.listingtable .python from=33 to=76 #lst:crossbars-class}

## EMU2751Aクラス

[EMU2751Aクラス](micropython/EMU2751A.py){.listingtable .python from=78 to=211 #lst:emu2751a-class}

::: rmnote

# hd44780compatモジュール

## BitFieldクラス

[](micropython/hd44780compat.py){.listingtable .python from=1 to=10}

## Registerクラス

[](micropython/hd44780compat.py){.listingtable .python from=11 to=20}

## HD44780Instructionsクラス

[](micropython/hd44780compat.py){.listingtable .python from=21 to=30}

# コード

::: LANDSCAPE

[GpakMuxモジュール全文](micropython/GpakMux.py){.listingtable .python}

\newpage

[MicroScpiDeviceモジュール全文](micropython/MicroScpiDevice.py){.listingtable .python}

\newpage

[EMU2751Aモジュール全文](micropython/EMU2751A.py){.listingtable .python}

:::

:::
