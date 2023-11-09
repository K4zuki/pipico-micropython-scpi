\toc

# Raspberry Pi Pico as SCPI instrument

#### Description {-}

This document is an API reference for an SCPI-ish device implemented on Raspberry Pi Pico or
any RP2040 based microcontroller boards. The device has programmed as Micropython library.

The RP2040 microcontroller has 2x I2C, 2x SPI, 2x UART, 16x PWM and 4x ADC peripherals multiplexed to 30x GPIOs.
In this implementation GPIO is limited down to 9, and there is no command for UART.
This primarily targets the Pico board and so that some GPIOs are reserved for other purpose and
no access from the API.

#### Tested devices {-}

- Raspberry Pi Pico
- Raspberry Pi Pico H

#### Untested devices {-}

- Raspberry Pi Pico W
- Raspberry Pi Pico WH

#### Installation, Question, Discussion, Contribution {-}

Write Micropython firmware, and put `main.py`, `MicroScpiDevice.py` and `RaspberryScpiPico.py` on root of target directory.

For any question, create an issue on github repo - https://github.com/K4zuki/pipico-micropython-scpi

#### Pico pinout {-}

Following tables [@tbl:pico-pinout] and [@tbl:special-functions] show function assignment for Pico.
There is also RP2040 GPIO# column applies to other third party boards.

::: {.table #tbl:special-functions width=[0.3,0.3,0.3]}

Table: API unavailable or special functioned GPIO pins

| RP2040 GPIO# | API subsystem | Note                                   |
|:------------:|:-------------:|----------------------------------------|
|      0       |      NA       | UART0 TX (not implemented)             |
|      1       |      NA       | UART0 RX (not implemented)             |
|      23      |      NA       | (Pico) Onboard DC-DC converter control |
|      24      |      NA       | (Pico) VBUS status readout             |
|      25      | LED, PIN, PWM | (Pico) Onboard LED                     |
|      29      |      ADC      | (Pico) VSYS/3 voltage readout          |

:::

\newpage

<div class="table" width="[0.2,0.2,0.1,0.1,0.2,0.2]" id="tbl:pico-pinout">

Table: Raspberry Pi Pico pinout and function assignment

|                                         Pico<br>Function | RP2040<br>GPIO# | Pico<br>Pin | Pico<br>Pin | RP2040<br>GPIO# | Pico<br>Function                                         |
|---------------------------------------------------------:|:---------------:|:-----------:|:-----------:|:---------------:|:---------------------------------------------------------|
|                                                 UART0 TX |        0        |      1      |     40      |                 | [VBUS]{custom-style="PowerPinStyle"}                     |
|                                                 UART0 RX |        1        |      2      |     39      |                 | [VSYS]{custom-style="PowerPinStyle"}                     |
|                     [GND]{custom-style="GroundPinStyle"} |                 |      3      |     38      |                 | [GND]{custom-style="GroundPinStyle"}                     |
| [[SPI0 SCK]{custom-style="SPIPinStyle"}](#spi-subsystem) |        2        |      4      |     37      |                 | 3V3 EN                                                   |
|  [[SPI0 TX]{custom-style="SPIPinStyle"}](#spi-subsystem) |        3        |      5      |     36      |                 | 3V3 OUT                                                  |
|  [[SPI0 RX]{custom-style="SPIPinStyle"}](#spi-subsystem) |        4        |      6      |     35      |                 | [[ADC VREF]{custom-style="ADCPinStyle"}](#adc-subsystem) |
|  [[SPI0 CS]{custom-style="SPIPinStyle"}](#spi-subsystem) |        5        |      7      |     34      |       28        | [[ADC2]{custom-style="ADCPinStyle"}](#adc-subsystem)     |
|                     [GND]{custom-style="GroundPinStyle"} |                 |      8      |     33      |                 | [[ADC GND]{custom-style="ADCPinStyle"}](#adc-subsystem)  |
| [[I2C1 SDA]{custom-style="I2CPinStyle"}](#i2c-subsystem) |        6        |      9      |     32      |       27        | [[ADC1]{custom-style="ADCPinStyle"}](#adc-subsystem)     |
| [[I2C1 SCL]{custom-style="I2CPinStyle"}](#i2c-subsystem) |        7        |     10      |     31      |       26        | [[ADC0]{custom-style="ADCPinStyle"}](#adc-subsystem)     |
| [[I2C0 SDA]{custom-style="I2CPinStyle"}](#i2c-subsystem) |        8        |     11      |     30      |                 | RUN                                                      |
| [[I2C0 SCL]{custom-style="I2CPinStyle"}](#i2c-subsystem) |        9        |     12      |     20      |       22        | [[PIN 22]{custom-style="GPIOPinStyle"}](#pin-subsystem)  |
|                     [GND]{custom-style="GroundPinStyle"} |                 |     13      |     29      |                 | [GND]{custom-style="GroundPinStyle"}                     |
| [[SPI1 SCK]{custom-style="SPIPinStyle"}](#spi-subsystem) |       10        |     14      |     28      |       21        | [[PIN 21]{custom-style="GPIOPinStyle"}](#pin-subsystem)  |
|  [[SPI1 TX]{custom-style="SPIPinStyle"}](#spi-subsystem) |       11        |     15      |     27      |       20        | [[PIN 20]{custom-style="GPIOPinStyle"}](#pin-subsystem)  |
|  [[SPI1 RX]{custom-style="SPIPinStyle"}](#spi-subsystem) |       12        |     16      |     26      |       19        | [[PIN 19]{custom-style="GPIOPinStyle"}](#pin-subsystem)  |
|  [[SPI1 CS]{custom-style="SPIPinStyle"}](#spi-subsystem) |       13        |     17      |     25      |       18        | [[PIN 18]{custom-style="GPIOPinStyle"}](#pin-subsystem)  |
|                     [GND]{custom-style="GroundPinStyle"} |                 |     18      |     24      |                 | [GND]{custom-style="GroundPinStyle"}                     |
|  [[PIN 14]{custom-style="GPIOPinStyle"}](#pin-subsystem) |       14        |     19      |     23      |       17        | [[PIN 17]{custom-style="GPIOPinStyle"}](#pin-subsystem)  |
|  [[PIN 15]{custom-style="GPIOPinStyle"}](#pin-subsystem) |       15        |     20      |     22      |       16        | [[PIN 16]{custom-style="GPIOPinStyle"}](#pin-subsystem)  |

</div>

# Parameter types

Parameter types in **`bold`** applies to this implementation.

[**`<NR1>`**]{#nr1}

:   Digits with an implied decimal point assumed at the right of the least-significant digit.

    Example: `273`

[`<NR2>`]{#nr2}

:   Digits with an explicit decimal point. Example: `27.3`

[`<NR3>`]{#nr3}

:   Digits with an explicit decimal point and an exponent. Example: `2.73E+02`

[**`<NR4>`**]{#nr4}

:   Hexadecimal, even number of digits without a negative sign `"-"`. Example: `DEAD BEAF C00F3E`

[`<NRf>`]{#nrf}

:   Extended format that includes `<NR1>`, `<NR2>`, and `<NR3>`. Examples: `273 27.3 2.73E+02`

[`<NRf+>`]{#nrf-plus}

:   Expanded decimal format that includes `<NRf>` and `MIN`, `MAX`. Examples: `273 27.3 2.73E+02 MAX`
:   `MIN` and `MAX` are the minimum and maximum limit values that are implicit in the range specification for the parameter.

[`<Bool>`]{#bool}

:   Boolean Data. Can be numeric `(0, 1)` or named `(OFF, ON)`.

[`<SPD>`]{#spd}

:   String Program Data. Programs string parameters enclosed in single or double quotes.

[`<CPD>`]{#cpd}

:   Character Program Data. Programs discrete parameters. Accepts both the short form and long form.

[`<CRD>`]{#crd}

:   Character Response Data. Returns discrete parameters. Only the short form of the parameter is returned.

[**`<AARD>`**]{#aard}

:   Arbitrary ASCII Response Data. Permits the return of undelimited 7-bit ASCII. This data type has an implied message terminator.

[`<Block>`]{#block}

:   Arbitrary Block Response Data. Permits the return of definite length and indefinite length arbitrary response data. This data type has an implied message terminator.

# MACHINE Subsystem

```{=openxml}
<w:sdt>
    <w:sdtContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:p>
            <w:r>
                <w:fldChar w:fldCharType="begin" w:dirty="true" />
                <w:instrText xml:space="preserve">TOC \o "2-2" \h \b ”machine-subsystem” \u</w:instrText>
                <w:fldChar w:fldCharType="separate" />
                <w:fldChar w:fldCharType="end" />
            </w:r>
        </w:p>
    </w:sdtContent>
</w:sdt>

```

## MACHINE:FREQuency {.unnumbered #machine-frequency}

#### Syntax {-}

`MACHINE:FREQuency <frequency>`

:   This command sets Pico's CPU clock frequency in Hz. `<frequency>` must be between 100MHz and 275MHz inclusive.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                      | Type                                    | Range of values                                                                    | Default value |
|-------------------------------------------|-----------------------------------------|------------------------------------------------------------------------------------|---------------|
| [\<frequency\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [100_000_000]{custom-style="NormalTok"} to [275_000_000]{custom-style="NormalTok"} | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`MACHINE:FREQ 250e6` [// CPU is overclocking at 250MHz]{custom-style="CommentTok"}
:::

## MACHINE:FREQuency? {.unnumbered #machine-frequency-query}

#### Syntax {-}

`MACHINE:FREQuency?`

:   This query returns Pico's CPU clock frequency in Hz.

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`MACHINE:FREQ?` [// Returns frequency in Hz]{custom-style="CommentTok"}

:   Typical Response: _`125000000`_

# PIN Subsystem

```{=openxml}
<w:sdt>
    <w:sdtContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:p>
            <w:r>
                <w:fldChar w:fldCharType="begin" w:dirty="true" />
                <w:instrText xml:space="preserve">TOC \o "2-2" \h \b ”pin-subsystem” \u</w:instrText>
                <w:fldChar w:fldCharType="separate" />
                <w:fldChar w:fldCharType="end" />
            </w:r>
        </w:p>
    </w:sdtContent>
</w:sdt>

```

## PIN:MODE {.unnumbered #pin-mode}

#### Syntax {-}

`PIN<pin>:MODE <mode>`

:   This command sets mode of specified IO pin.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                 | Type                                    | Values                                                    | Default value |
|--------------------------------------|-----------------------------------------|-----------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"}  | [[NR1]{custom-style="NormalTok"}](#nr1) | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"} | N/A           |
| [\<mode\>]{custom-style="NormalTok"} | [[CRD]{custom-style="NormalTok"}](#crd) | [INput/OUTput/ODrain/PWM]{custom-style="NormalTok"}       | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:MODE OUTput` [// Sets Pin14 to output mode]{custom-style="CommentTok"}
:::

## PIN:MODE? {.unnumbered #pin-mode-query}

#### Syntax {-}

`PIN<pin>:MODE?`

:   This query returns status of specified IO pin's mode.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                    | Default value |
|-------------------------------------|-----------------------------------------|-----------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<CRD\>]{custom-style="NormalTok"}](#crd)

#### Example {-}

`PIN14:MODE?` [// Returns Pin14 pin mode]{custom-style="CommentTok"}

:   Typical Response: _`INput`_

## PIN:VALue {.unnumbered #pin-value}

#### Syntax {-}

`PIN<pin>:VALue <value>`

:   This command sets logical value of specified IO pin.
Numeric `1` and string `ON` sets logic HI. Numeric `0` and string `OFF` sets logic LO.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                  | Type                                      | Values                                                    | Default value |
|---------------------------------------|-------------------------------------------|-----------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"}   | [[NR1]{custom-style="NormalTok"}](#nr1)   | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"} | N/A           |
| [\<value\>]{custom-style="NormalTok"} | [[Bool]{custom-style="NormalTok"}](#bool) |                                                           | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:VAL ON` [// Sets Pin14 to logic HI]{custom-style="CommentTok"} \
`PIN14:VALue 0` [// Sets Pin14 to logic LO]{custom-style="CommentTok"}
:::

## PIN:VALue? {.unnumbered #pin-value-query}

#### Syntax {-}

`PIN<pin>:VALue?`

:   This query returns logical value of specified IO pin. `ON` is a logic HI, `OFF` is a logic LO.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                    | Default value |
|-------------------------------------|-----------------------------------------|-----------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<Bool\>]{custom-style="NormalTok"}](#bool)

#### Example {-}

`PIN14:VAL?` [// Returns Pin14 pin value]{custom-style="CommentTok"}

:   Typical Response: _`ON`_

## PIN:ON {.unnumbered #pin-on}

#### Syntax {-}

`PIN<pin>:ON`

:   This command sets logical value of specified IO pin to logic HI.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                    | Default value |
|-------------------------------------|-----------------------------------------|-----------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:ON` [// Sets Pin14 to logic HI]{custom-style="CommentTok"} \
:::

## PIN:OFF {.unnumbered #pin-off}

#### Syntax {-}

`PIN<pin>:OFF`

:   This command sets logical value of specified IO pin to logic LO.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                    | Default value |
|-------------------------------------|-----------------------------------------|-----------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:OFF` [// Sets Pin14 to logic LO]{custom-style="CommentTok"} \
:::

## PIN:PWM:FREQuency {.unnumbered #pin-pwm-frequency}

#### Syntax {-}

`PIN<pin>:PWM:FREQuency <frequency>`

:   This command sets PWM frequency of specified IO pin in Hz.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                      | Type                                    | Values                                                                  | Default value |
|-------------------------------------------|-----------------------------------------|-------------------------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"}       | [[NR1]{custom-style="NormalTok"}](#nr1) | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"}               | N/A           |
| [\<frequency\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [1000]{custom-style="NormalTok"} to [100_000]{custom-style="NormalTok"} | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:PWM:FREQ 55555` [// Pin14 PWM frequency is set at 55555Hz]{custom-style="CommentTok"}
:::

## PIN:PWM:FREQuency? {.unnumbered #pin-pwm-frequency-query}

#### Syntax {-}

`PIN<pin>:PWM:FREQuency?`

:   This query returns PWM frequency of specified IO pin in Hz.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                    | Default value |
|-------------------------------------|-----------------------------------------|-----------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`PIN14:PWM:FREQ?` [// Returns Pin14 PWM frequency in Hz]{custom-style="CommentTok"}

:   Typical Response: _`500000`_

## PIN:PWM:DUTY {.unnumbered #pin-pwm-duty}

#### Syntax {-}

`PIN<pin>:PWM:DUTY <duty>`

:   This command sets PWM duty of specified IO pin in range of 1 to 65535.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                 | Type                                    | Values                                                             | Default value |
|--------------------------------------|-----------------------------------------|--------------------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"}  | [[NR1]{custom-style="NormalTok"}](#nr1) | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"}          | N/A           |
| [\<duty\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [1]{custom-style="NormalTok"} to [65535]{custom-style="NormalTok"} | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:PWM:DUTY 25252` [// Pin14 PWM duty is set at 25252 out of 65535]{custom-style="CommentTok"}
:::

## PIN:PWM:DUTY? {.unnumbered #pin-pwm-duty-query}

#### Syntax {-}

`PIN<pin>:PWM:DUTY?`

:   This query returns PWM duty of specified IO pin in range of 1 to 65535

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                    | Default value |
|-------------------------------------|-----------------------------------------|-----------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [14/15/16/17/18/19/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`PIN14:PWM:DUTY?` [// Returns Pin14 PWM duty in integer]{custom-style="CommentTok"}

:   Typical Response: _`32768`_

# LED Subsystem

```{=openxml}
<w:sdt>
    <w:sdtContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:p>
            <w:r>
                <w:fldChar w:fldCharType="begin" w:dirty="true" />
                <w:instrText xml:space="preserve">TOC \o "2-2" \h \b ”led-subsystem” \u</w:instrText>
                <w:fldChar w:fldCharType="separate" />
                <w:fldChar w:fldCharType="end" />
            </w:r>
        </w:p>
    </w:sdtContent>
</w:sdt>

```

## LED:ON {.unnumbered #led-on}

#### Syntax {-}

`LED:ON`

:   This command turns onboard LED on.

## LED:OFF {.unnumbered #led-off}

#### Syntax {-}

`LED:OFF`

:   This command turns onboard LED off.

## LED:VALue {.unnumbered #led-value}

#### Syntax {-}

`LED:VALue <value>`

:   This command sets logical value of onboard LED. Numeric `1` and string `ON` turns on.
Numeric `0` and string `OFF` turns off.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                  | Type                                      | Values | Default value |
|---------------------------------------|-------------------------------------------|--------|---------------|
| [\<value\>]{custom-style="NormalTok"} | [[Bool]{custom-style="NormalTok"}](#bool) |        | N/A           |

</div>

## LED:VALue? {.unnumbered #led-value-query}

#### Syntax {-}

`LED:VALue?`

:   This query returns logical value of onboard LED.

#### Returned Query Format {-}

[[\<Bool\>]{custom-style="NormalTok"}](#bool)

#### Example {-}

`LED:VALue?`

:   Typical Response: _`ON`_

## LED:PWM:ENable {.unnumbered #led-pwm-enable}

#### Syntax {-}

`LED:PWM:ENable`

:   This command enables PWM output for onboard LED.

## LED:PWM:DISable {.unnumbered #led-pwm-disable}

#### Syntax {-}

`LED:PWM:DISable`

:   This command disables PWM output for onboard LED.

## LED:PWM:FREQuency {.unnumbered #led-pwm-frequency}

#### Syntax {-}

`LED:PWM:FREQuency <frequency>`

:   This command sets PWM frequency of onboard LED in Hz.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                      | Type                                    | Values                                                                  | Default value |
|-------------------------------------------|-----------------------------------------|-------------------------------------------------------------------------|---------------|
| [\<frequency\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [1000]{custom-style="NormalTok"} to [100_000]{custom-style="NormalTok"} | N/A           |

</div>

## LED:PWM:FREQuency? {.unnumbered #led-pwm-frequency-query}

#### Syntax {-}

`LED:PWM:FREQuency?`

:   This query returns PWM frequency of onboard LED in Hz.

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`LED:PWM:FREQ?` [// Returns Pin14 PWM frequency in Hz]{custom-style="CommentTok"}

:   Typical Response: _`500000`_

## LED:PWM:DUTY {.unnumbered #led-pwm-duty}

#### Syntax {-}

`LED:PWM:DUTY <duty>`

:   This command sets PWM duty of onboard LED in range of 1 to 65535.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                 | Type                                    | Values                                                             | Default value |
|--------------------------------------|-----------------------------------------|--------------------------------------------------------------------|---------------|
| [\<duty\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [1]{custom-style="NormalTok"} to [65535]{custom-style="NormalTok"} | N/A           |

</div>

## LED:PWM:DUTY? {.unnumbered #led-pwm-duty-query}

#### Syntax {-}

`LED:PWM:DUTY?`

:   This query returns PWM duty of onboard LED in range of 1 to 65535.

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`LED:DUTY?` [// Returns LED PWM duty in integer]{custom-style="CommentTok"}

:   Typical Response: _`32768`_

# I2C Subsystem

```{=openxml}
<w:sdt>
    <w:sdtContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:p>
            <w:r>
                <w:fldChar w:fldCharType="begin" w:dirty="true" />
                <w:instrText xml:space="preserve">TOC \o "2-2" \h \b ”i2c-subsystem” \u</w:instrText>
                <w:fldChar w:fldCharType="separate" />
                <w:fldChar w:fldCharType="end" />
            </w:r>
        </w:p>
    </w:sdtContent>
</w:sdt>

```

## I2C:SCAN? {.unnumbered #i2c-scan-query}

#### Syntax {-}

`I2C<bus>:SCAN?`

:   This query returns list of I2C slave device on the specified bus.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR4\>\[,\<NR4\>\]]{custom-style="NormalTok"}](#nr4)

#### Example {-}

`I2C0:SCAN?` [// Scans slave devices on I2C0 bus]{custom-style="CommentTok"}

:   Typical Response: _`A6,5A,80,EE`_ when 8-bit addressing. _`53,2D,40,77`_ when 7-bit addressing

## I2C:FREQuency {.unnumbered #i2c-frequency}

#### Syntax {-}

`I2C<bus>:FREQuency <frequency>`

:   This command sets clock frequency of specified bus.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                      | Type                                    | Values                                                                    | Default value |
|-------------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}       | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<frequency\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [10_000]{custom-style="NormalTok"} to [400_000]{custom-style="NormalTok"} | N/A           |

</div>

## I2C:FREQuency? {.unnumbered #i2c-frequency-query}

#### Syntax {-}

`I2C<bus>:FREQuency?`

:   This query returns clock frequency of specified bus.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`I2C1:FREQuency?` [// Returns bus clock frequency setting in Hz]{custom-style="CommentTok"}

:   Typical Response: _`400000`_

## I2C:ADDRess:BIT {.unnumbered #i2c-address-bit}

#### Syntax {-}

`I2C<bus>:ADDRess:BIT <bit>`

:   This command sets addressing of specified bus.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                                                                          | Default value |
|-------------------------------------|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                                       | N/A           |
| [\<bit\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus addressing.<br>[0]{custom-style="NormalTok"} is 7-bit addressing,<br>[1]{custom-style="NormalTok"} is 8-bit | N/A           |

</div>

## I2C:ADDRess:BIT? {.unnumbered #i2c-address-bit-query}

#### Syntax {-}

`I2C<bus>:ADDRess:BIT?`

:   This query returns addressing of specified bus.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`I2C0:ADDRess:BIT?` [// Returns addressing setting in integer]{custom-style="CommentTok"}

:   Typical Response: _`0`_

## I2C:WRITE {.unnumbered #i2c-write}

#### Syntax {-}

`I2C<bus>:WRITE <address>,<buffer>,<stop>`

:   This command writes list of hexadecimal to specified slave device on the bus.
Stop condition is configured by `<stop>`.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                    | Type                                                   | Values                                                                                                                                                                     | Default value |
|-----------------------------------------|--------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}     | [[NR1]{custom-style="NormalTok"}](#nr1)                | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                                                                                                  | N/A           |
| [\<address\>]{custom-style="NormalTok"} | [[NR4]{custom-style="NormalTok"}](#nr4)                | [02]{custom-style="NormalTok"} to [FC]{custom-style="NormalTok"} (8-bit addressing)<br>[01]{custom-style="NormalTok"} to [7E]{custom-style="NormalTok"} (7-bit addressing) | N/A           |
| [\<buffer\>]{custom-style="NormalTok"}  | [[\<NR4\>\[\<NR4\>\]]{custom-style="NormalTok"}](#nr4) |                                                                                                                                                                            | N/A           |
| [\<stop\>]{custom-style="NormalTok"}    | [[NR1]{custom-style="NormalTok"}](#nr1)                | [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                                                                                                             | N/A           |

</div>

## I2C:READ? {.unnumbered #i2c-read-query}

#### Syntax {-}

`I2C<bus>:READ? <address>,<length>,<stop>`

:   This query reads `<length>` bytes of data from specified slave device on the bus.
Stop condition is configured by `<stop>`.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                    | Type                                    | Values                                                                                                                                                                     | Default value |
|-----------------------------------------|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}     | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                                                                                                  | N/A           |
| [\<address\>]{custom-style="NormalTok"} | [[NR4]{custom-style="NormalTok"}](#nr4) | [02]{custom-style="NormalTok"} to [FC]{custom-style="NormalTok"} (8-bit addressing)<br>[01]{custom-style="NormalTok"} to [7E]{custom-style="NormalTok"} (7-bit addressing) | N/A           |
| [\<length\>]{custom-style="NormalTok"}  | [[NR1]{custom-style="NormalTok"}](#nr1) | 1 or larger                                                                                                                                                                | N/A           |
| [\<stop\>]{custom-style="NormalTok"}    | [[NR1]{custom-style="NormalTok"}](#nr1) | [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                                                                                                             | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR4\>\[,\<NR4\>\]]{custom-style="NormalTok"}](#nr4)

#### Example {-}

`I2C0:READ? AA,4,1` [// Returns 4-bytes of data from slave device in list of hexadecimal texts]{custom-style="CommentTok"}

:   Typical Response: _`DE,AD,BE,EF`_

## I2C:MEMory:WRITE {.unnumbered #i2c-memory-write}

#### Syntax {-}

`I2C<bus>:MEMory:WRITE <address>,<memaddress>,`<br>`<buffer>,<addrsize>`

:   This command sends stream of hexadecimal data into specified memory address of slave device.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                       | Type                                                   | Values                                                                                                                                                                     | Default value |
|--------------------------------------------|--------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}        | [[NR1]{custom-style="NormalTok"}](#nr1)                | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                                                                                                  | N/A           |
| [\<address\>]{custom-style="NormalTok"}    | [[NR4]{custom-style="NormalTok"}](#nr4)                | [02]{custom-style="NormalTok"} to [FC]{custom-style="NormalTok"} (8-bit addressing)<br>[01]{custom-style="NormalTok"} to [7E]{custom-style="NormalTok"} (7-bit addressing) | N/A           |
| [\<memaddress\>]{custom-style="NormalTok"} | [[NR4]{custom-style="NormalTok"}](#nr4)                | [00]{custom-style="NormalTok"} to [FF]{custom-style="NormalTok"}                                                                                                           | N/A           |
| [\<buffer\>]{custom-style="NormalTok"}     | [[\<NR4\>\[\<NR4\>\]]{custom-style="NormalTok"}](#nr4) | Stream of data                                                                                                                                                             | N/A           |
| [\<addrsize\>]{custom-style="NormalTok"}   | [[NR1]{custom-style="NormalTok"}](#nr1)                | [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                                                                                                             | N/A           |

</div>

## I2C:MEMory:READ? {.unnumbered #i2c-memory-read-query}

#### Syntax {-}

`I2C<bus>:MEMory:READ? <address>,<memaddress>,`<br>`<nbytes>,<addrsize>`

:   This query returns comma separated list of hexadecimal data stored in specific memory address of
the target I2C slave slave device.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                       | Type                                    | Values                                                                                                                                                                     | Default value |
|--------------------------------------------|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}        | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                                                                                                  | N/A           |
| [\<address\>]{custom-style="NormalTok"}    | [[NR4]{custom-style="NormalTok"}](#nr4) | [02]{custom-style="NormalTok"} to [FC]{custom-style="NormalTok"} (8-bit addressing)<br>[01]{custom-style="NormalTok"} to [7E]{custom-style="NormalTok"} (7-bit addressing) | N/A           |
| [\<memaddress\>]{custom-style="NormalTok"} | [[NR4]{custom-style="NormalTok"}](#nr4) | [00]{custom-style="NormalTok"} to [FF]{custom-style="NormalTok"}                                                                                                           | N/A           |
| [\<nbytes\>]{custom-style="NormalTok"}     | [[NR1]{custom-style="NormalTok"}](#nr4) | 1 or larger                                                                                                                                                                | N/A           |
| [\<addrsize\>]{custom-style="NormalTok"}   | [[NR1]{custom-style="NormalTok"}](#nr1) | [1]{custom-style="NormalTok"} or [2]{custom-style="NormalTok"}                                                                                                             | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR4\>\[,\<NR4\>\]]{custom-style="NormalTok"}](#nr4)

#### Example {-}

`I2C1:MEMory:READ? 55,AA,4,1`  [// Returns 4-bytes of data from register 0xAA of slave device]{custom-style="CommentTok"}

:   Typical Response: _`DE,AD,BE,EF`_

# SPI Subsystem

```{=openxml}
<w:sdt>
    <w:sdtContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:p>
            <w:r>
                <w:fldChar w:fldCharType="begin" w:dirty="true" />
                <w:instrText xml:space="preserve">TOC \o "2-2" \h \b ”spi-subsystem” \u</w:instrText>
                <w:fldChar w:fldCharType="separate" />
                <w:fldChar w:fldCharType="end" />
            </w:r>
        </w:p>
    </w:sdtContent>
</w:sdt>

```

## SPI:CSEL:POLarity {.unnumbered #spi-csel-polarity}

#### Syntax {-}

`SPI<bus>:CSEL:POLarity <polarity>`

:   This command sets chip select polarity for specified SPI bus

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                     | Type                                      | Values                                                                                                         | Default value |
|------------------------------------------|-------------------------------------------|----------------------------------------------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}      | [[NR1]{custom-style="NormalTok"}](#nr1)   | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                                      | N/A           |
| [\<polarity\>]{custom-style="NormalTok"} | [[Bool]{custom-style="NormalTok"}](#bool) | Chip select polarity. [1]{custom-style="NormalTok"} is HI-active<br>[0]{custom-style="NormalTok"} is LO-active | N/A           |

</div>

#### Example {-}

`SPI0:CSEL:POLarity 1` [// Sets SPI0 chip select to HI-active]{custom-style="CommentTok"}

## SPI:CSEL:POLarity? {.unnumbered #spi-csel-polarity-query}

#### Syntax {-}

`SPI<bus>:CSEL:POLarity?`

:   This query returns chip select pin polarity for specified SPI bus

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<Bool\>]{custom-style="NormalTok"}](#bool)

#### Example {-}

`SPI0:CSEL:POLarity?` [// Returns SPI0 chip select polarity]{custom-style="CommentTok"}

:   Typical Response: _`1`_

## SPI:CSEL:VALue {-}

#### Syntax {-}

`SPI<bus>:CSEL:VALue <value>`

:   This command sets logical value of chip select pin for specified bus.
Numeric `1` and string `ON` selects bus. Numeric `0` and string `OFF` deselects bus.
Chip select polarity is set by [[SPI:CSEL:POLarity]{custom-style="NormalTok"}](#spi-csel-polarity) command

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                  | Type                                      | Values                                                                    | Default value |
|---------------------------------------|-------------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}   | [[NR1]{custom-style="NormalTok"}](#nr1)   | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<value\>]{custom-style="NormalTok"} | [[Bool]{custom-style="NormalTok"}](#bool) | Logical value of CS pin.                                                  | N/A           |

</div>

## SPI:CSEL:VALue? {-}

#### Syntax {-}

`SPI<bus>:CSEL:VALue?`

:   This query returns logical value of CS pin. `ON` is selecting bus, `OFF` is deselecting.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<CRD\>]{custom-style="NormalTok"}](#crd)

#### Example {-}

`SPI0:CSEL:VALue?` [// Returns chip select pin value]{custom-style="CommentTok"}

:   Typical Response: _`OFF`_

## SPI:MODE {-}

#### Syntax {-}

`SPI<bus>:MODE <mode>`

:   This command sets bus clock and phase mode for specified SPI bus

    | Mode  | CPOL |  CPHA   |
    |:-----:|:----:|:-------:|
    | **0** | Low  | Rising  |
    | **1** | Low  | Falling |
    | **2** | High | Rising  |
    | **3** | High | Falling |

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                 | Type                                    | Values                                                                                                  | Default value |
|--------------------------------------|-----------------------------------------|---------------------------------------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}  | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                               | N/A           |
| [\<mode\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus clock and phase mode [0/1/2/3]{custom-style="NormalTok"} or <br>[DEFault]{custom-style="NormalTok"} | N/A           |

</div>

## SPI:MODE? {-}

#### Syntax {-}

`SPI<bus>:MODE?`

:   This query returns bus clock and phase mode for specified SPI bus

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`SPI1:MODE?` [// Returns clock and phase mode for bus 1]{custom-style="CommentTok"}

:   Typical Response: _`2`_

## SPI:FREQuency {-}

#### Syntax {-}

`SPI<bus>:FREQuency <frequency>`

:   This command sets bus clock frequency for specified bus.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                      | Type                                    | Values                                                                       | Default value |
|-------------------------------------------|-----------------------------------------|------------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}       | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}    | N/A           |
| [\<frequency\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [10_000]{custom-style="NormalTok"} to [10_000_000]{custom-style="NormalTok"} | N/A           |

</div>

## SPI:FREQuency? {-}

#### Syntax {-}

`SPI<bus>:FREQuency?`

:   This query returns bus clock frequency for specified bus.

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`SPI0:FREQuency?` [// Returns SPI0 bus clock frequency in integer]{custom-style="CommentTok"}

:   Typical Response: _`5000000`_

## SPI:TRANSfer {-}

#### Syntax {-}

`SPI<bus>:TRANSfer <data>,<pre_cs>,<post_cs>`

:   This command transfers

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                    | Type                                      | Values                                                                    | Default value |
|-----------------------------------------|-------------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}     | [[NR1]{custom-style="NormalTok"}](#nr1)   | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<data\>]{custom-style="NormalTok"}    | [[NR1]{custom-style="NormalTok"}](#nr1)   |                                                                           | N/A           |
| [\<pre_cs\>]{custom-style="NormalTok"}  | [[Bool]{custom-style="NormalTok"}](#bool) |                                                                           | N/A           |
| [\<post_cs\>]{custom-style="NormalTok"} | [[Bool]{custom-style="NormalTok"}](#bool) |                                                                           | N/A           |

</div>

## SPI:WRITE {-}

#### Syntax {-}

`SPI<bus>:WRITE <data>,<pre_cs>,<post_cs>`

:   This command

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                    | Type                                      | Values                                                                    | Default value |
|-----------------------------------------|-------------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}     | [[NR1]{custom-style="NormalTok"}](#nr1)   | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<data\>]{custom-style="NormalTok"}    | [[NR1]{custom-style="NormalTok"}](#nr1)   |                                                                           | N/A           |
| [\<pre_cs\>]{custom-style="NormalTok"}  | [[Bool]{custom-style="NormalTok"}](#bool) |                                                                           | N/A           |
| [\<post_cs\>]{custom-style="NormalTok"} | [[Bool]{custom-style="NormalTok"}](#bool) |                                                                           | N/A           |

</div>

## SPI:READ? {-}

#### Syntax {-}

`SPI<bus>:READ? <length>,<mask>,<pre_cs>,<post_cs>`

:   This query returns

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                    | Type                                      | Values                                                                    | Default value |
|-----------------------------------------|-------------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}     | [[NR1]{custom-style="NormalTok"}](#nr1)   | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<length\>]{custom-style="NormalTok"}  | [[NR1]{custom-style="NormalTok"}](#nr1)   |                                                                           | N/A           |
| [\<mask\>]{custom-style="NormalTok"}    | [[NR1]{custom-style="NormalTok"}](#nr1)   |                                                                           | N/A           |
| [\<pre_cs\>]{custom-style="NormalTok"}  | [[Bool]{custom-style="NormalTok"}](#bool) |                                                                           | N/A           |
| [\<post_cs\>]{custom-style="NormalTok"} | [[Bool]{custom-style="NormalTok"}](#bool) |                                                                           | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`SPI0:READ? 1,AA` [// Returns Pin14 PWM duty in integer]{custom-style="CommentTok"}

:   Typical Response: _`32768`_

# ADC Subsystem

```{=openxml}
<w:sdt>
    <w:sdtContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:p>
            <w:r>
                <w:fldChar w:fldCharType="begin" w:dirty="true" />
                <w:instrText xml:space="preserve">TOC \o "2-2" \h \b ”adc-subsystem” \u</w:instrText>
                <w:fldChar w:fldCharType="separate" />
                <w:fldChar w:fldCharType="end" />
            </w:r>
        </w:p>
    </w:sdtContent>
</w:sdt>

```

## ADC:READ? {.unnumbered #adc-read-query}

#### Syntax {-}

`ADC<channel>:READ?`

:   This query returns ADC conversion value in range of 0 to 65535

#### Parameter {-}

<div class="table" width="[0.15,0.15,0.5,0.25]">

| Item                                    | Type                                    | Values                              | Default value |
|-----------------------------------------|-----------------------------------------|-------------------------------------|---------------|
| [\<channel\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [0/1/2/3]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`ADC2:READ?` [// Returns voltage at ADC2 in 16bit unsigned integer]{custom-style="CommentTok"}

:   Typical Response: _`32768`_

# IEEE-488.2 Common Commands {#ieee4882-common-commands}

```{=openxml}
<w:sdt>
    <w:sdtContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:p>
            <w:r>
                <w:fldChar w:fldCharType="begin" w:dirty="true" />
                <w:instrText xml:space="preserve">TOC \o "2-2" \h \b ”ieee4882-common-commands” \u</w:instrText>
                <w:fldChar w:fldCharType="separate" />
                <w:fldChar w:fldCharType="end" />
            </w:r>
        </w:p>
    </w:sdtContent>
</w:sdt>

```

## \*IDN? {.unnumbered #idn}

#### Syntax {-}

`*IDN?`

:   This command reads the instrument's identification string which contains four
comma-separated fields. The first field is the manufacturer's name, the second is
the model number of the instrument, the third is the serial number, and the fourth
is the firmware revision which contains three firmwares separated by dashes.

#### Returned Query Format {-}

[[\<AARD\>]{custom-style="NormalTok"}](#aard)

#### Example {-}

`*IDN?` [// Returns the instrument's identification string]{custom-style="CommentTok"}

:   Typical Response: `"RaspberryPiPico,RP001,{serial},0.0.1"`

## \*RST {.unnumbered #rst}

#### Syntax {-}

`*RST`

:   This command resets the target device, including System clock,
GPIO mode and state, I2C and SPI bus clock, SPI chip select pin polarity and state.

#### Example {-}

`*RST` [// Resets the target device including CPU clock.]{custom-style="CommentTok"}

:   Typical Response: `"Soft reset"`
