\newpage

# まえがき {-}

## このドキュメントは何 {-}

この本は、「勝手にアプリケーションノート4」で設計製作したリレーマトリクスHATを応用し、既存のSCPIデバイス"U2751A"をエミュレートするまでを解説
したドキュメントです。SCPIのふりをする部分はラズピコ(Raspberry Pi pico)が行います。ラズピコの開発はMicroPythonとPyCharmで行いました。

エミュレートとは言っても、SCPI・IEEE488の厳密な準拠はしていません。たとえばセミコロンで数珠つなぎする部分などの実装はバッサリカットしましたし、
エラーハンドリングもけっこう適当です。

また、非常に残念なことに、GreenPakの石を作っていたDialog社はルネサスに買われてしまいました。**もう直販もありません。**
Mouserではかろうじて一部の石を売っていますが、GreenPAKから派生した**ForgeFPGAの開発キットをディスコンにした**あたりからすると、もう先はないのかもしれません。
この本が出される2022年12月31日がD社が登記上？存在する最後の日です。少なくとも日本では。

そういうとこやぞ&#174;

\toc

# SCPIエミュレーション方針

## 割り切り

- **SCPIの完全な実装は目指さない**
- ;でつないでも最初だけ解釈

# スイッチマトリクス「Agilent/Keysight U2751A」

## コマンド一覧

::: {.table width=[0.4,0.4,0.2]}

| SCPI                            | Parameter             | Implemented |
|---------------------------------|-----------------------|-------------|
| `DIAGnostic:RELay:CYCLes?`      | None                  | False       |
| `DIAGnostic:RELay:CYCLes:CLEar` | None                  | False       |
| `ROUTe:CLOSe`                   | `(@101,102:105,201:)` | True        |
| `ROUTe:CLOSe?`                  | `(@101,102:105,201:)` | True        |
| `ROUTe:OPEN`                    | `(@101,102:105,201:)` | True        |
| `ROUTe:OPEN?`                   | `(@101,102:105,201:)` | True        |
| `SYSTem:CDEScription?`          | None                  | False       |
| `SYSTem:ERRor?`                 | None                  | False       |
| `SYSTem:VERSion?`               | None                  | False       |
| `*CLS`                          | None                  | False       |
| `*ESE/*ESE?`                    | None                  | False       |
| `*ESR?`                         | None                  | False       |
| `*IDN?`                         | None                  | True        |
| `*OPC/*OPC?`                    | None                  | False       |
| `*RST`                          | None                  | False       |
| `*SRE/*SRE?`                    | None                  | False       |
| `*STB?`                         | None                  | False       |
| `*TST?`                         | None                  | False       |

:::

# GpakMuxモジュール

[](micropython/GpakMux.py){.listingtable .python from=1 to=10}

# MicroScpiDeviceモジュール

## ScpiKeywordクラス

[](micropython/MicroScpiDevice.py){.listingtable .python from=8 to=30}

## ScpiCommandクラス

[](micropython/MicroScpiDevice.py){.listingtable .python from=33 to=39}

## MicroScpiDeviceクラス

[](micropython/MicroScpiDevice.py){.listingtable .python from=44 to=94}

# EMU2751Aモジュール

## CrossBarsクラス

[](micropython/EMU2751A.py){.listingtable .python from=33 to=76}

## EMU2751Aクラス

[](micropython/EMU2751A.py){.listingtable .python from=78 to=211}

::: rmnote

# hd44780compatモジュール

## BitFieldクラス

[](micropython/hd44780compat.py){.listingtable .python from=1 to=10}

## Registerクラス

[](micropython/hd44780compat.py){.listingtable .python from=11 to=20}

## HD44780Instructionsクラス

[](micropython/hd44780compat.py){.listingtable .python from=21 to=30}

:::

# コード

::: LANDSCAPE

[GpakMuxモジュール全文](micropython/GpakMux.py){.listingtable .python}

\newpage

[MicroScpiDeviceモジュール全文](micropython/MicroScpiDevice.py){.listingtable .python}

\newpage

[EMU2751Aモジュール全文](micropython/EMU2751A.py){.listingtable .python}

:::
