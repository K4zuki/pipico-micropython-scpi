\toc

# Numbers

`<NR1>`

:   Digits with an implied decimal point assumed at the right of the least-significant digit.

    Example: `273`

`<NR2>`

:   Digits with an explicit decimal point. Example: `27.3`

`<NR3>`

:   Digits with an explicit decimal point and an exponent. Example: `2.73E+02`

`<NRf>`

:   Extended format that includes `<NR1>`, `<NR2>`, and `<NR3>`. Examples: `273 27.3 2.73E+02`

`<NRf+>`

:   Expanded decimal format that includes `<NRf>` and `MIN`, `MAX`. Examples: `273 27.3 2.73E+02 MAX`

`MIN` and `MAX` are the minimum and maximum limit values that are implicit in the range specification for the parameter.

`<Bool>`

:   Boolean Data. Can be numeric `(0, 1)` or named `(OFF, ON)`.

`<SPD>`

:   String Program Data. Programs string parameters enclosed in single or double quotes.

`<CPD>`

:   Character Program Data. Programs discrete parameters. Accepts both the short form and long form.

`<SRD>`

:   String Response Data. Returns string parameters enclosed in single or double quotes.

`<CRD>`

:   Character Response Data. Returns discrete parameters. Only the short form of the parameter is returned.

`<AARD>`

:   Arbitrary ASCII Response Data. Permits the return of undelimited 7-bit ASCII. This data type has an implied message terminator.

`<Block>`

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

#### Parameter {-}

<div class="table" widths="[0.25,0.1,0.35,0.25]">

| Item                                      | Type | Range of values                | Default value |
|-------------------------------------------|------|--------------------------------|---------------|
| [\<frequency\>]{custom-style="NormalTok"} | NR1  | `100_000_000` to `275_000_000` | N/A           |

: notitle {.notitle}
</div>

#### Example {-}

## MACHINE:FREQuency? {-}

#### Syntax {-}

`MACHINE:FREQuency?`

#### Returned Query Format {-}

`<NR1>`

#### Example {-}

Typical Response: `125000000`

# PIN Subsystem

## PIN:MODE {-}

## PIN:MODE? {-}

## PIN:VALue {-}

## PIN:VALue? {-}

## PIN:ON {-}

## PIN:OFF {-}

## PIN:PWM:FREQuency {-}

## PIN:PWM:FREQuency? {-}

## PIN:PWM:DUTY {-}

## PIN:PWM:DUTY? {-}

# LED Subsystem

## LED:ON {-}

## LED:OFF {-}

## LED:VALue {-}

## LED:VALue? {-}

## LED:PWM:ENable {-}

## LED:PWM:DISable {-}

## LED:PWM:FREQuency {-}

## LED:PWM:FREQuency? {-}

## LED:PWM:DUTY {-}

## LED:PWM:DUTY? {-}

# I2C Subsystem

## I2C:SCAN? {-}

## I2C:FREQuency {-}

## I2C:FREQuency? {-}

## I2C:ADDRess:BIT {-}

## I2C:ADDRess:BIT? {-}

## I2C:WRITE {-}

## I2C:READ? {-}

## I2C:MEMory:WRITE {-}

## I2C:MEMory:READ {-}

# SPI Subsystem

## SPI:CSEL:POLarity {-}

## SPI:CSEL:POLarity? {-}

## SPI:CSEL:VALue {-}

## SPI:MODE {-}

## SPI:MODE? {-}

## SPI:FREQuency {-}

## SPI:FREQuency? {-}

## SPI:TRANSfer {-}

## SPI:WRITE {-}

## SPI:READ? {-}

# ADC Subsystem

## ADC:READ? {-}

# IEEE-488.2 Common Commands

## \*IDN? {-}

#### Syntax {-}

- \*IDN?

This command reads the instrument's identification string which contains four\
comma-separated fields. The first field is the manufacturer's name, the second is\
the model number of the instrument, the third is the serial number, and the fourth\
is the firmware revision which contains three firmwares separated by dashes.

#### Returned Query Format {-}

- \<AARD\>

> The command returns a string with the following format.
>
> `KEYSIGHT TECHNOLOGIES,U2751A,<Serial Number>,Va.aa-b.bb-c.cc`

#### Example {-}

The following query returns the instrument's identification string.

`*IDN?`

#### Typical Response {-}

`KEYSIGHT TECHNOLOGIES,U2751A,MY12345678,V1.00-1.00-1.00`

If the system is unable to recognize the model number or serial number, the \*IDN? command will return the default value of the model and serial number. Please perform self-test for error check.
