\toc

# Raspberry Pi Pico as SCPI instrument

# Parameter types

[`<NR1>`]{#nr1}

:   Digits with an implied decimal point assumed at the right of the least-significant digit.

    Example: `273`

[`<NR2>`]{#nr2}

:   Digits with an explicit decimal point. Example: `27.3`

[`<NR3>`]{#nr3}

:   Digits with an explicit decimal point and an exponent. Example: `2.73E+02`

[`<NR4>`]{#nr4}

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

[`<AARD>`]{#aard}

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

## MACHINE:FREQuency {-}

#### Syntax {-}

`MACHINE:FREQuency <frequency>`

:   This command sets Pico's CPU clock frequency in Hz. `<frequency>` must be between 100MHz and 275MHz inclusive.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                      | Type                                    | Range of values                                                                    | Default value |
|-------------------------------------------|-----------------------------------------|------------------------------------------------------------------------------------|---------------|
| [\<frequency\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [100_000_000]{custom-style="NormalTok"} to [275_000_000]{custom-style="NormalTok"} | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`MACHINE:FREQ 250e6` [// CPU is overclocking at 250MHz]{custom-style="CommentTok"}
:::

## MACHINE:FREQuency? {-}

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

## PIN:MODE {-}

#### Syntax {-}

`PIN<pin>:MODE <mode>`

:   This command sets mode of specified IO pin.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                 | Type                                    | Values                                              | Default value |
|--------------------------------------|-----------------------------------------|-----------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"}  | [[NR1]{custom-style="NormalTok"}](#nr1) | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"}   | N/A           |
| [\<mode\>]{custom-style="NormalTok"} | [[CRD]{custom-style="NormalTok"}](#crd) | [INput/OUTput/ODrain/PWM]{custom-style="NormalTok"} | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:MODE OUTput` [// Sets Pin14 to output mode]{custom-style="CommentTok"}
:::

## PIN:MODE? {-}

#### Syntax {-}

`PIN<pin>:MODE?`

:   This query returns status of specified IO pin's mode.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                            | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<CRD\>]{custom-style="NormalTok"}](#crd)

#### Example {-}

`PIN14:MODE?` [// Returns Pin14 pin mode]{custom-style="CommentTok"}

:   Typical Response: _`INput`_

## PIN:VALue {-}

#### Syntax {-}

`PIN<pin>:VALue <value>`

:   This command sets logical value of of specified IO pin.
Numeric `1` and string `ON` sets logic HI. Numeric `0` and string `OFF` sets logic LO.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                  | Type                                      | Values                                            | Default value |
|---------------------------------------|-------------------------------------------|---------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"}   | [[NR1]{custom-style="NormalTok"}](#nr1)   | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"} | N/A           |
| [\<value\>]{custom-style="NormalTok"} | [[Bool]{custom-style="NormalTok"}](#bool) |                                                   | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:VAL ON` [// Sets Pin14 to logic HI]{custom-style="CommentTok"} \
`PIN14:VALue 0` [// Sets Pin14 to logic LO]{custom-style="CommentTok"}
:::

## PIN:VALue? {-}

#### Syntax {-}

`PIN<pin>:VALue?`

:   This query returns logical value of specified IO pin. `ON` is a logic HI, `OFF` is a logic LO.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                            | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<CRD\>]{custom-style="NormalTok"}](#crd)

#### Example {-}

`PIN14:VAL?` [// Returns Pin14 pin value]{custom-style="CommentTok"}

:   Typical Response: _`ON`_

## PIN:ON {-}

#### Syntax {-}

`PIN<pin>:ON`

:   This command sets logical value of specified IO pin to logic HI.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                            | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

## PIN:OFF {-}

#### Syntax {-}

`PIN<pin>:OFF`

:   This command sets logical value of specified IO pin to logic LO.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                            | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

## PIN:PWM:FREQuency {-}

#### Syntax {-}

`PIN<pin>:PWM:FREQuency <frequency>`

:   This command sets PWM frequency of specified IO pin in Hz.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                      | Type                                    | Values                                                                  | Default value |
|-------------------------------------------|-----------------------------------------|-------------------------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"}       | [[NR1]{custom-style="NormalTok"}](#nr1) | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"}                       | N/A           |
| [\<frequency\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [1000]{custom-style="NormalTok"} to [100_000]{custom-style="NormalTok"} | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:FREQ 55555` [// Pin14 PWM frequency is set at 55555Hz]{custom-style="CommentTok"}
:::

## PIN:PWM:FREQuency? {-}

#### Syntax {-}

`PIN<pin>:PWM:FREQuency?`

:   This query returns PWM frequency of specified IO pin in Hz.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                            | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`PIN14:PWM:FREQ?` [// Returns Pin14 PWM frequency in Hz]{custom-style="CommentTok"}

:   Typical Response: _`500000`_

## PIN:PWM:DUTY {-}

#### Syntax {-}

`PIN<pin>:PWM:DUTY <duty>`

:   This command sets PWM duty of specified IO pin in range of 1 to 65535.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                 | Type                                    | Values                                                             | Default value |
|--------------------------------------|-----------------------------------------|--------------------------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"}  | [[NR1]{custom-style="NormalTok"}](#nr1) | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"}                  | N/A           |
| [\<duty\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [1]{custom-style="NormalTok"} to [65535]{custom-style="NormalTok"} | N/A           |

</div>

#### Example {-}

:::{custom-style="Definition Term"}
`PIN14:DUTY 25252` [// Pin14 PWM duty is set at 25252 out of 65535]{custom-style="CommentTok"}
:::

## PIN:PWM:DUTY? {-}

#### Syntax {-}

`PIN<pin>:PWM:DUTY?`

:   This query returns PWM duty of specified IO pin in range of 1 to 65535

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                            | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------|---------------|
| [\<pin\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [6/7/14/15/20/21/22/25]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

`PIN14:DUTY?` [// Returns Pin14 PWM duty in integer]{custom-style="CommentTok"}

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

## LED:ON {-}

#### Syntax {-}

`LED:ON`

:   This command turns onboard LED on.

## LED:OFF {-}

#### Syntax {-}

`LED:OFF`

:   This command turns onboard LED off.

## LED:VALue {-}

#### Syntax {-}

`LED:VALue <value>`

:   This command sets logical value of onboard LED. Numeric `1` and string `ON` turns on.
Numeric `0` and string `OFF` turns off.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                  | Type                                      | Values | Default value |
|---------------------------------------|-------------------------------------------|--------|---------------|
| [\<value\>]{custom-style="NormalTok"} | [[Bool]{custom-style="NormalTok"}](#bool) |        | N/A           |

</div>

## LED:VALue? {-}

#### Syntax {-}

`LED:VALue?`

:   This query returns logical value of onboard LED.

#### Returned Query Format {-}

[[\<CRD\>]{custom-style="NormalTok"}](#crd)

#### Example {-}

`LED:VALue?`

:   Typical Response: _`ON`_

## LED:PWM:ENable {-}

#### Syntax {-}

`LED:PWM:ENable`

:   This command enables PWM output for onboard LED.

## LED:PWM:DISable {-}

#### Syntax {-}

`LED:PWM:DISable`

:   This command disables PWM output for onboard LED.

## LED:PWM:FREQuency {-}

#### Syntax {-}

`LED:PWM:FREQuency <frequency>`

:   This command sets PWM frequency of onboard LED in Hz.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                      | Type                                    | Values                                                                  | Default value |
|-------------------------------------------|-----------------------------------------|-------------------------------------------------------------------------|---------------|
| [\<frequency\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [1000]{custom-style="NormalTok"} to [100_000]{custom-style="NormalTok"} | N/A           |

</div>

## LED:PWM:FREQuency? {-}

#### Syntax {-}

`LED:PWM:FREQuency?`

:   This query returns PWM frequency of onboard LED in Hz.

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

Typical Response: _`500000`_

## LED:PWM:DUTY {-}

#### Syntax {-}

`LED:PWM:DUTY <duty>`

:   This command sets PWM duty of onboard LED in range of 1 to 65535.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                 | Type                                    | Values                                                             | Default value |
|--------------------------------------|-----------------------------------------|--------------------------------------------------------------------|---------------|
| [\<duty\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [1]{custom-style="NormalTok"} to [65535]{custom-style="NormalTok"} | N/A           |

</div>

## LED:PWM:DUTY? {-}

#### Syntax {-}

`LED:PWM:DUTY?`

:   This query returns PWM duty of onboard LED in range of 1 to 65535.

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

Typical Response: _`32768`_

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

## I2C:SCAN? {-}

#### Syntax {-}

`I2C<bus>:SCAN?`

:   This query returns list of I2C slave device on the specified bus.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[`<NR4>[,<NR4>]`](#nr4)

#### Example {-}

Typical Response: _`A6,5A,80,EE`_ when 8-bit addressing. _`53,2D,40,77`_ when 7-bit addressing

## I2C:FREQuency {-}

#### Syntax {-}

`I2C<bus>:FREQuency <frequency>`

:   This command sets clock frequency of specified bus.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                      | Type                                    | Values                                                                    | Default value |
|-------------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}       | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<frequency\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | [10_000]{custom-style="NormalTok"} to [400_000]{custom-style="NormalTok"} | N/A           |

</div>

## I2C:FREQuency? {-}

#### Syntax {-}

`I2C<bus>:FREQuency?`

:   This query returns clock frequency of specified bus.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

Typical Response: _`400000`_

## I2C:ADDRess:BIT {-}

#### Syntax {-}

`I2C<bus>:ADDRess:BIT <bit>`

:   This command sets addressing of specified bus.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                                                                         | Default value |
|-------------------------------------|-----------------------------------------|------------------------------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}                      | N/A           |
| [\<bit\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus addressing. [0]{custom-style="NormalTok"} is 7-bit, [1]{custom-style="NormalTok"} is 8-bit | N/A           |

</div>

## I2C:ADDRess:BIT? {-}

#### Syntax {-}

`I2C<bus>:ADDRess:BIT?`

:   This query returns addressing of specified bus.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                | Type                                    | Values                                                                    | Default value |
|-------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |

</div>

#### Returned Query Format {-}

[[\<NR1\>]{custom-style="NormalTok"}](#nr1)

#### Example {-}

Typical Response: _`0`_

## I2C:WRITE {-}

#### Syntax {-}

`I2C<bus>:WRITE <address>,<buffer>,<stop>`

:   This command writes list of hexadecimal to specified slave device on the bus.
Stop condition is configured by `<stop>`.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                    | Type                                    | Values                                                                    | Default value |
|-----------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}     | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<address\>]{custom-style="NormalTok"} | [[NR4]{custom-style="NormalTok"}](#nr4) | [01]{custom-style="NormalTok"} to [FF]{custom-style="NormalTok"}          | N/A           |
| [\<buffer\>]{custom-style="NormalTok"}  | [[NR4]{custom-style="NormalTok"}](#nr4) |                                                                           | N/A           |
| [\<stop\>]{custom-style="NormalTok"}    | [[NR1]{custom-style="NormalTok"}](#nr1) | [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}`           | N/A           |

</div>

## I2C:READ? {-}

#### Syntax {-}

`I2C<bus>:READ? <address>,<length>,<stop>`

:   This query reads `<length>` bytes of data from specified slave device on the bus. \
Stop condition is configured by `<stop>`.

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                   | Type                                    | Values                                                                    | Default value |
|----------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}    | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<length\>]{custom-style="NormalTok"} | [[NR1]{custom-style="NormalTok"}](#nr1) | 1 or larger                                                               | N/A           |
| [\<stop\>]{custom-style="NormalTok"}   | [[NR1]{custom-style="NormalTok"}](#nr1) | [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}            | N/A           |

</div>

#### Returned Query Format {-}

[`<NR4>[,<NR4>]`](#nr4)

#### Example {-}

Typical Response: _`DE,AD,BE,EF`_

## I2C:MEMory:WRITE {-}

#### Syntax {-}

`I2C<bus>:MEMory:WRITE <address>,<memaddress>,<buffer>,<addrsize>`

This command sets

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                       | Type                                    | Values                                                                    | Default value |
|--------------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}        | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<address\>]{custom-style="NormalTok"}    | [[NR4]{custom-style="NormalTok"}](#nr4) | [01]{custom-style="NormalTok"} to [FF]{custom-style="NormalTok"}          | N/A           |
| [\<memaddress\>]{custom-style="NormalTok"} | [[NR4]{custom-style="NormalTok"}](#nr4) | [00]{custom-style="NormalTok"} to [FF]{custom-style="NormalTok"}          | N/A           |
| [\<buffer\>]{custom-style="NormalTok"}     | [[NR4]{custom-style="NormalTok"}](#nr4) |                                                                           | N/A           |
| [\<addrsize\>]{custom-style="NormalTok"}   | [[NR1]{custom-style="NormalTok"}](#nr1) | [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"}            | N/A           |

</div>

## I2C:MEMory:READ {-}

#### Syntax {-}

`I2C<bus>:MEMory:READ? <address>,<memaddress>,<nbytes>,<addrsize>`

This query returns

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                       | Type                                    | Values                                                                    | Default value |
|--------------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|---------------|
| [\<bus\>]{custom-style="NormalTok"}        | [[NR1]{custom-style="NormalTok"}](#nr1) | Bus number [0]{custom-style="NormalTok"} or [1]{custom-style="NormalTok"} | N/A           |
| [\<address\>]{custom-style="NormalTok"}    | [[NR4]{custom-style="NormalTok"}](#nr4) | [01]{custom-style="NormalTok"} to [FF]{custom-style="NormalTok"}          | N/A           |
| [\<memaddress\>]{custom-style="NormalTok"} | [[NR4]{custom-style="NormalTok"}](#nr4) | [00]{custom-style="NormalTok"} to [FF]{custom-style="NormalTok"}          | N/A           |
| [\<nbytes\>]{custom-style="NormalTok"}     | [[NR1]{custom-style="NormalTok"}](#nr4) | 1 or larger                                                               | N/A           |
| [\<addrsize\>]{custom-style="NormalTok"}   | [[NR1]{custom-style="NormalTok"}](#nr1) | [1]{custom-style="NormalTok"} or [2]{custom-style="NormalTok"}            | N/A           |

</div>

#### Returned Query Format {-}

[`<NR4>[,<NR4>]`](#nr4)

#### Example {-}

Typical Response: _`DE,AD,BE,EF`_

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

## SPI:CSEL:POLarity {-}

## SPI:CSEL:POLarity? {-}

## SPI:CSEL:VALue {-}

## SPI:CSEL:VALue? {-}

## SPI:MODE {-}

## SPI:MODE? {-}

## SPI:FREQuency {-}

## SPI:FREQuency? {-}

## SPI:TRANSfer {-}

## SPI:WRITE {-}

## SPI:READ? {-}

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

## ADC:READ? {-}

# IEEE-488.2 Common Commands

## \*IDN? {-}

#### Syntax {-}

`*IDN?`

This command reads the instrument's identification string which contains four
comma-separated fields. The first field is the manufacturer's name, the second is
the model number of the instrument, the third is the serial number, and the fourth
is the firmware revision which contains three firmwares separated by dashes.

#### Returned Query Format {-}

`<AARD>`

> The command returns a string with the following format.
>
> `KEYSIGHT TECHNOLOGIES,U2751A,<Serial Number>,Va.aa-b.bb-c.cc`

#### Example {-}

The following query returns the instrument's identification string.

`*IDN?`

#### Typical Response {-}

`"RaspberryPiPico,RP001,{serial},0.0.1"`

If the system is unable to recognize the model number or serial number,
the \*IDN? command will return the default value of the model and serial number.
Please perform self-test for error check.

## \*RST
