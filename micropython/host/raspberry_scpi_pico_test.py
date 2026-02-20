"""
MIT License

Copyright (c) 2023 Kazuki Yamamoto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
"""
*CLS <No Param>
*ESE/*ESE? <No Param>
*ESR? <No Param>
*IDN? <No Param>
*OPC/*OPC? <No Param>
*RST <No Param>
*SRE/*SRE? <No Param>
*STB? <No Param>
*TST? <No Param>

MACHINE:FREQuency[?] num|DEFault|MINimum|MAXimum

SYSTem:ERRor?

PIN?
PIN[14|15|16|17|18|19|20|21|22|25]:MODE[?] INput|OUTput|ODrain|PWM|DEFault
PIN[14|15|16|17|18|19|20|21|22|25]:VALue[?] 0|1|OFF|ON|DEFault
PIN[14|15|16|17|18|19|20|21|22|25]:ON
PIN[14|15|16|17|18|19|20|21|22|25]:OFF

PWM?
PWM[14|15|16|17|18|19|20|21|22|25]:ON
PWM[14|15|16|17|18|19|20|21|22|25]:OFF
PWM[14|15|16|17|18|19|20|21|22|25]:FREQuency[?] num|DEFault|MINimum|MAXimum
PWM[14|15|16|17|18|19|20|21|22|25]:DUTY[?] num|DEFault|MINimum|MAXimum

LED?
LED:ON
LED:OFF
LED:VALue[?] 0|1|OFF|ON|DEFault
LED:PWM:ON
LED:PWM:OFF
LED:PWM:FREQuency[?] num|DEFault|MINimum|MAXimum
LED:PWM:DUTY[?] num|DEFault|MINimum|MAXimum

I2C?
I2C[01]:SCAN?
I2C[01]:FREQuency[?] num|DEFault|MINimum|MAXimum
I2C[01]:ADDRess:BIT[?] 0|1|DEFault
I2C[01]:WRITE address,buffer,stop
I2C[01]:READ? address,length,stop
I2C[01]:MEMory:WRITE address,memaddress,buffer,addrsize
I2C[01]:MEMory:READ address,memaddress,nbytes,addrsize

SPI?
SPI[01]:CSEL:POLarity[?] 0|1|DEFault
SPI[01]:CSEL:VALue[?] 0|1|OFF|ON
SPI[01]:MODE[?] 0|1|2|3|DEFault
SPI[01]:FREQuency[?] num|DEFault|MINimum|MAXimum
SPI[01]:TRANSfer data,pre_cs,post_cs
SPI[01]:WRITE data,pre_cs,post_cs
SPI[01]:READ? length,mask,pre_cs,post_cs

ADC[01234]:READ?
"""
import sys
import time

# from port_config import port_name

scpi_commands = [
    "*IDN?",
    "MACHINE:FREQuency?",
    "MACHINE:FREQuency 250e6",

    "SYSTem:ERRor?",

    "PI",
    "PIN?",

    "PIN14:MODE?", "PIN14:MODE INput", "PIN14:MODE OUTput", "PIN14:MODE ODrain", "PIN14:MODE PWM", "PIN14:MODE DEFault",
    "PIN15:MODE?", "PIN15:MODE INput", "PIN15:MODE OUTput", "PIN15:MODE ODrain", "PIN15:MODE PWM", "PIN15:MODE DEFault",
    "PIN16:MODE?", "PIN16:MODE INput", "PIN16:MODE OUTput", "PIN16:MODE ODrain", "PIN16:MODE PWM", "PIN16:MODE DEFault",
    "PIN17:MODE?", "PIN17:MODE INput", "PIN17:MODE OUTput", "PIN17:MODE ODrain", "PIN17:MODE PWM", "PIN17:MODE DEFault",
    "PIN18:MODE?", "PIN18:MODE INput", "PIN18:MODE OUTput", "PIN18:MODE ODrain", "PIN18:MODE PWM", "PIN18:MODE DEFault",
    "PIN19:MODE?", "PIN19:MODE INput", "PIN19:MODE OUTput", "PIN19:MODE ODrain", "PIN19:MODE PWM", "PIN19:MODE DEFault",
    "PIN20:MODE?", "PIN20:MODE INput", "PIN20:MODE OUTput", "PIN20:MODE ODrain", "PIN20:MODE PWM", "PIN20:MODE DEFault",
    "PIN21:MODE?", "PIN21:MODE INput", "PIN21:MODE OUTput", "PIN21:MODE ODrain", "PIN21:MODE PWM", "PIN21:MODE DEFault",
    "PIN22:MODE?", "PIN22:MODE INput", "PIN22:MODE OUTput", "PIN22:MODE ODrain", "PIN22:MODE PWM", "PIN22:MODE DEFault",
    "PIN25:MODE?", "PIN25:MODE INput", "PIN25:MODE OUTput", "PIN25:MODE ODrain", "PIN25:MODE PWM", "PIN25:MODE DEFault",

    "PIN14:VALue?", "PIN14:VALue 0", "PIN14:VALue 1", "PIN14:VALue OFF", "PIN14:VALue ON", "PIN14:VALue DEFault",
    "PIN15:VALue?", "PIN15:VALue 0", "PIN15:VALue 1", "PIN15:VALue OFF", "PIN15:VALue ON", "PIN15:VALue DEFault",
    "PIN16:VALue?", "PIN16:VALue 0", "PIN16:VALue 1", "PIN16:VALue OFF", "PIN16:VALue ON", "PIN16:VALue DEFault",
    "PIN17:VALue?", "PIN17:VALue 0", "PIN17:VALue 1", "PIN17:VALue OFF", "PIN17:VALue ON", "PIN17:VALue DEFault",
    "PIN18:VALue?", "PIN18:VALue 0", "PIN18:VALue 1", "PIN18:VALue OFF", "PIN18:VALue ON", "PIN18:VALue DEFault",
    "PIN19:VALue?", "PIN19:VALue 0", "PIN19:VALue 1", "PIN19:VALue OFF", "PIN19:VALue ON", "PIN19:VALue DEFault",
    "PIN20:VALue?", "PIN20:VALue 0", "PIN20:VALue 1", "PIN20:VALue OFF", "PIN20:VALue ON", "PIN20:VALue DEFault",
    "PIN21:VALue?", "PIN21:VALue 0", "PIN21:VALue 1", "PIN21:VALue OFF", "PIN21:VALue ON", "PIN21:VALue DEFault",
    "PIN22:VALue?", "PIN22:VALue 0", "PIN22:VALue 1", "PIN22:VALue OFF", "PIN22:VALue ON", "PIN22:VALue DEFault",
    "PIN25:VALue?", "PIN25:VALue 0", "PIN25:VALue 1", "PIN25:VALue OFF", "PIN25:VALue ON", "PIN25:VALue DEFault",

    "PIN14:OFF", "PIN14:ON", "PIN14:OFF",
    "PIN15:OFF", "PIN15:ON", "PIN15:OFF",
    "PIN16:OFF", "PIN16:ON", "PIN16:OFF",
    "PIN17:OFF", "PIN17:ON", "PIN17:OFF",
    "PIN18:OFF", "PIN18:ON", "PIN18:OFF",
    "PIN19:OFF", "PIN19:ON", "PIN19:OFF",
    "PIN20:OFF", "PIN20:ON", "PIN20:OFF",
    "PIN21:OFF", "PIN21:ON", "PIN21:OFF",
    "PIN22:OFF", "PIN22:ON", "PIN22:OFF",
    "PIN25:OFF", "PIN25:ON", "PIN25:OFF",

    "PWM?",

    "PWM14:FREQuency?", "PWM14:FREQuency 12345", "PWM14:FREQuency?",
    "PWM15:FREQuency?", "PWM15:FREQuency 12345", "PWM15:FREQuency?",
    "PWM16:FREQuency?", "PWM16:FREQuency 12345", "PWM16:FREQuency?",
    "PWM17:FREQuency?", "PWM17:FREQuency 12345", "PWM17:FREQuency?",
    "PWM18:FREQuency?", "PWM18:FREQuency 12345", "PWM18:FREQuency?",
    "PWM19:FREQuency?", "PWM19:FREQuency 12345", "PWM19:FREQuency?",
    "PWM20:FREQuency?", "PWM20:FREQuency 12345", "PWM20:FREQuency?",
    "PWM21:FREQuency?", "PWM21:FREQuency 12345", "PWM21:FREQuency?",
    "PWM22:FREQuency?", "PWM22:FREQuency 12345", "PWM22:FREQuency?",
    "PWM25:FREQuency?", "PWM25:FREQuency 12345", "PWM25:FREQuency?",
    "PWM14:FREQuency? MIN", "PWM14:FREQuency? DEF", "PWM14:FREQuency? MAX",
    "PWM15:FREQuency? MIN", "PWM15:FREQuency? DEF", "PWM15:FREQuency? MAX",
    "PWM16:FREQuency? MIN", "PWM16:FREQuency? DEF", "PWM16:FREQuency? MAX",
    "PWM17:FREQuency? MIN", "PWM17:FREQuency? DEF", "PWM17:FREQuency? MAX",
    "PWM18:FREQuency? MIN", "PWM18:FREQuency? DEF", "PWM18:FREQuency? MAX",
    "PWM19:FREQuency? MIN", "PWM19:FREQuency? DEF", "PWM19:FREQuency? MAX",
    "PWM20:FREQuency? MIN", "PWM20:FREQuency? DEF", "PWM20:FREQuency? MAX",
    "PWM21:FREQuency? MIN", "PWM21:FREQuency? DEF", "PWM21:FREQuency? MAX",
    "PWM22:FREQuency? MIN", "PWM22:FREQuency? DEF", "PWM22:FREQuency? MAX",
    "PWM25:FREQuency? MIN", "PWM25:FREQuency? DEF", "PWM25:FREQuency? MAX",
    "PWM14:FREQuency MIN", "PWM14:FREQuency?",
    "PWM15:FREQuency MIN", "PWM15:FREQuency?",
    "PWM16:FREQuency MIN", "PWM16:FREQuency?",
    "PWM17:FREQuency MIN", "PWM17:FREQuency?",
    "PWM18:FREQuency MIN", "PWM18:FREQuency?",
    "PWM19:FREQuency MIN", "PWM19:FREQuency?",
    "PWM20:FREQuency MIN", "PWM20:FREQuency?",
    "PWM21:FREQuency MIN", "PWM21:FREQuency?",
    "PWM22:FREQuency MIN", "PWM22:FREQuency?",
    "PWM25:FREQuency MIN", "PWM25:FREQuency?",
    "PWM14:FREQuency DEF", "PWM14:FREQuency?",
    "PWM15:FREQuency DEF", "PWM15:FREQuency?",
    "PWM16:FREQuency DEF", "PWM16:FREQuency?",
    "PWM17:FREQuency DEF", "PWM17:FREQuency?",
    "PWM18:FREQuency DEF", "PWM18:FREQuency?",
    "PWM19:FREQuency DEF", "PWM19:FREQuency?",
    "PWM20:FREQuency DEF", "PWM20:FREQuency?",
    "PWM21:FREQuency DEF", "PWM21:FREQuency?",
    "PWM22:FREQuency DEF", "PWM22:FREQuency?",
    "PWM25:FREQuency DEF", "PWM25:FREQuency?",
    "PWM14:FREQuency MAX", "PWM14:FREQuency?",
    "PWM15:FREQuency MAX", "PWM15:FREQuency?",
    "PWM16:FREQuency MAX", "PWM16:FREQuency?",
    "PWM17:FREQuency MAX", "PWM17:FREQuency?",
    "PWM18:FREQuency MAX", "PWM18:FREQuency?",
    "PWM19:FREQuency MAX", "PWM19:FREQuency?",
    "PWM20:FREQuency MAX", "PWM20:FREQuency?",
    "PWM21:FREQuency MAX", "PWM21:FREQuency?",
    "PWM22:FREQuency MAX", "PWM22:FREQuency?",
    "PWM25:FREQuency MAX", "PWM25:FREQuency?",

    "PWM14:DUTY? MINimum", "PWM14:DUTY? MAXimum", "PWM14:DUTY? DEFault",
    "PWM15:DUTY? MINimum", "PWM15:DUTY? MAXimum", "PWM15:DUTY? DEFault",
    "PWM16:DUTY? MINimum", "PWM16:DUTY? MAXimum", "PWM16:DUTY? DEFault",
    "PWM17:DUTY? MINimum", "PWM17:DUTY? MAXimum", "PWM17:DUTY? DEFault",
    "PWM18:DUTY? MINimum", "PWM18:DUTY? MAXimum", "PWM18:DUTY? DEFault",
    "PWM19:DUTY? MINimum", "PWM19:DUTY? MAXimum", "PWM19:DUTY? DEFault",
    "PWM20:DUTY? MINimum", "PWM20:DUTY? MAXimum", "PWM20:DUTY? DEFault",
    "PWM21:DUTY? MINimum", "PWM21:DUTY? MAXimum", "PWM21:DUTY? DEFault",
    "PWM22:DUTY? MINimum", "PWM22:DUTY? MAXimum", "PWM22:DUTY? DEFault",
    "PWM25:DUTY? MINimum", "PWM25:DUTY? MAXimum", "PWM25:DUTY? DEFault",

    "PWM14:DUTY?", "PWM14:DUTY 12345",
    "PWM15:DUTY?", "PWM15:DUTY 12345",
    "PWM16:DUTY?", "PWM16:DUTY 12345",
    "PWM17:DUTY?", "PWM17:DUTY 12345",
    "PWM18:DUTY?", "PWM18:DUTY 12345",
    "PWM19:DUTY?", "PWM19:DUTY 12345",
    "PWM20:DUTY?", "PWM20:DUTY 12345",
    "PWM21:DUTY?", "PWM21:DUTY 12345",
    "PWM22:DUTY?", "PWM22:DUTY 12345",
    "PWM25:DUTY?", "PWM25:DUTY 12345",

    "PWM14:DUTY MINimum", "PWM14:DUTY?", "PWM14:DUTY DEFault", "PWM14:DUTY?", "PWM14:DUTY MAXimum", "PWM14:DUTY?",
    "PWM15:DUTY MINimum", "PWM15:DUTY?", "PWM15:DUTY DEFault", "PWM15:DUTY?", "PWM15:DUTY MAXimum", "PWM15:DUTY?",
    "PWM16:DUTY MINimum", "PWM16:DUTY?", "PWM16:DUTY DEFault", "PWM16:DUTY?", "PWM16:DUTY MAXimum", "PWM16:DUTY?",
    "PWM17:DUTY MINimum", "PWM17:DUTY?", "PWM17:DUTY DEFault", "PWM17:DUTY?", "PWM17:DUTY MAXimum", "PWM17:DUTY?",
    "PWM18:DUTY MINimum", "PWM18:DUTY?", "PWM18:DUTY DEFault", "PWM18:DUTY?", "PWM18:DUTY MAXimum", "PWM18:DUTY?",
    "PWM19:DUTY MINimum", "PWM19:DUTY?", "PWM19:DUTY DEFault", "PWM19:DUTY?", "PWM19:DUTY MAXimum", "PWM19:DUTY?",
    "PWM20:DUTY MINimum", "PWM20:DUTY?", "PWM20:DUTY DEFault", "PWM20:DUTY?", "PWM20:DUTY MAXimum", "PWM20:DUTY?",
    "PWM21:DUTY MINimum", "PWM21:DUTY?", "PWM21:DUTY DEFault", "PWM21:DUTY?", "PWM21:DUTY MAXimum", "PWM21:DUTY?",
    "PWM22:DUTY MINimum", "PWM22:DUTY?", "PWM22:DUTY DEFault", "PWM22:DUTY?", "PWM22:DUTY MAXimum", "PWM22:DUTY?",
    "PWM25:DUTY MINimum", "PWM25:DUTY?", "PWM25:DUTY DEFault", "PWM25:DUTY?", "PWM25:DUTY MAXimum", "PWM25:DUTY?",

    "PWM14:DUTY?", "PWM14:DUTY DEFault", "PWM14:DUTY?",
    "PWM15:DUTY?", "PWM15:DUTY DEFault", "PWM15:DUTY?",
    "PWM16:DUTY?", "PWM16:DUTY DEFault", "PWM16:DUTY?",
    "PWM17:DUTY?", "PWM17:DUTY DEFault", "PWM17:DUTY?",
    "PWM18:DUTY?", "PWM18:DUTY DEFault", "PWM18:DUTY?",
    "PWM19:DUTY?", "PWM19:DUTY DEFault", "PWM19:DUTY?",
    "PWM20:DUTY?", "PWM20:DUTY DEFault", "PWM20:DUTY?",
    "PWM21:DUTY?", "PWM21:DUTY DEFault", "PWM21:DUTY?",
    "PWM22:DUTY?", "PWM22:DUTY DEFault", "PWM22:DUTY?",
    "PWM25:DUTY?", "PWM25:DUTY DEFault", "PWM25:DUTY?",

    "PWM14:DUTY?", "PWM14:DUTY MAXimum", "PWM14:DUTY?",
    "PWM15:DUTY?", "PWM15:DUTY MAXimum", "PWM15:DUTY?",
    "PWM16:DUTY?", "PWM16:DUTY MAXimum", "PWM16:DUTY?",
    "PWM17:DUTY?", "PWM17:DUTY MAXimum", "PWM17:DUTY?",
    "PWM18:DUTY?", "PWM18:DUTY MAXimum", "PWM18:DUTY?",
    "PWM19:DUTY?", "PWM19:DUTY MAXimum", "PWM19:DUTY?",
    "PWM20:DUTY?", "PWM20:DUTY MAXimum", "PWM20:DUTY?",
    "PWM21:DUTY?", "PWM21:DUTY MAXimum", "PWM21:DUTY?",
    "PWM22:DUTY?", "PWM22:DUTY MAXimum", "PWM22:DUTY?",
    "PWM25:DUTY?", "PWM25:DUTY MAXimum", "PWM25:DUTY?",

    "PWM14:ON", "PWM14:OFF",
    "PWM15:ON", "PWM15:OFF",
    "PWM16:ON", "PWM16:OFF",
    "PWM17:ON", "PWM17:OFF",
    "PWM18:ON", "PWM18:OFF",
    "PWM19:ON", "PWM19:OFF",
    "PWM20:ON", "PWM20:OFF",
    "PWM21:ON", "PWM21:OFF",
    "PWM22:ON", "PWM22:OFF",
    "PWM25:ON", "PWM25:OFF",

    "LED?",
    "LED:VALue OFF", "LED:VALue ON", "LED:OFF", "LED:ON",
    "LED:PWM:FREQuency 12345", "LED:PWM:FREQuency?", "LED:PWM:DUTY?", "LED:PWM:DUTY 12345",
    "LED:PWM:ON", "LED:PWM:OFF",
    "ADC0:READ?", "ADC1:READ?", "ADC2:READ?", "ADC3:READ?", "ADC4:READ?",

    "I2C?",
    "I2C0:SCAN?", "I2C0:FREQuency?", "I2C0:FREQuency 114514",
    "I2C1:SCAN?", "I2C1:FREQuency?", "I2C1:FREQuency 114514",

    "I2C0:ADDRess:BIT?", "I2C0:ADDRess:BIT 0", "I2C0:ADDRess:BIT 1", "I2C0:ADDRess:BIT 3", "I2C0:ADDRess:BIT DEFault",
    "I2C1:ADDRess:BIT?", "I2C1:ADDRess:BIT 0", "I2C1:ADDRess:BIT 1", "I2C1:ADDRess:BIT 3", "I2C1:ADDRess:BIT DEFault",
    "I2C0:ADDRess:BIT 0", "I2C0:ADDRess:BIT?", "I2C0:READ AA,10,1",
    "I2C1:ADDRess:BIT 0", "I2C1:ADDRess:BIT?", "I2C1:READ AA,10,1",
    "I2C0:ADDRess:BIT 1", "I2C0:ADDRess:BIT?", "I2C0:READ AA,10,1",
    "I2C1:ADDRess:BIT 1", "I2C1:ADDRess:BIT?", "I2C1:READ AA,10,1",

    "I2C0:WRITE 10,7aAA,1",
    "I2C0:READ? 10,1,1",
    "I2C1:WRITE 10,7aAA,1",
    "I2C1:READ? 10,1,1",
    "I2C0:WRITE 10,0000,0", "I2C0:READ? 10,1,1",
    "I2C1:WRITE 10,0000,0", "I2C1:READ? 10,1,1",
    "I2C0:WRITE 10,0000,0", "I2C0:READ? 10,1,1",
    "I2C1:WRITE 10,0000,0", "I2C1:READ? 10,256,1",

    "I2C0:MEMory:WRITE 10,7A,aa,1", "I2C1:MEMory:WRITE 10,7A,aa,1",
    "I2C0:MEMory:READ? 10,7A,1,1", "I2C1:MEMory:READ? 10,7A,1,1",

    "I2C1:MEMory:WRITE 10,7A,bb,1",
    "I2C1:MEMory:READ? 10,00,256,1",

    "SPI?",
    "SPI0:CSEL:POLarity?", "SPI0:CSEL:POLarity 0", "SPI0:CSEL:POLarity 1", "SPI0:CSEL:POLarity DEFault",
    "SPI1:CSEL:POLarity?", "SPI1:CSEL:POLarity 0", "SPI1:CSEL:POLarity 1", "SPI1:CSEL:POLarity DEFault",
    "SPI0:CSEL:VALue 0", "SPI0:CSEL:VALue?", "SPI0:CSEL:VALue 1", "SPI0:CSEL:VALue?", "SPI0:CSEL:VALue OFF",
    "SPI0:CSEL:VALue?", "SPI0:CSEL:VALue ON", "SPI0:CSEL:VALue?",
    "SPI1:CSEL:VALue 0", "SPI1:CSEL:VALue?", "SPI1:CSEL:VALue 1", "SPI1:CSEL:VALue?", "SPI1:CSEL:VALue OFF",
    "SPI1:CSEL:VALue?", "SPI1:CSEL:VALue ON", "SPI1:CSEL:VALue?",
    "SPI0:MODE?", "SPI0:MODE 0", "SPI0:MODE 1", "SPI0:MODE?", "SPI0:MODE 2", "SPI0:MODE?", "SPI0:MODE 3", "SPI0:MODE?",
    "SPI0:MODE DEFault", "SPI0:MODE?", "SPI0:MODE", "SPI0:MODE 5", "SPI0:MODE A",
    "SPI1:MODE?", "SPI1:MODE 0", "SPI1:MODE 1", "SPI1:MODE?", "SPI1:MODE 2", "SPI1:MODE?", "SPI1:MODE 3", "SPI1:MODE?",
    "SPI1:MODE DEFault", "SPI1:MODE?", "SPI1:MODE", "SPI1:MODE 5", "SPI1:MODE A",
    "SPI0:FREQuency?", "SPI0:FREQuency 123456",
    "SPI1:FREQuency?", "SPI1:FREQuency 123456",
    "SPI0:WRITE 12345,ON,OFF", "SPI0:WRITE 123456,ON,OFF",
    "SPI1:WRITE 12345,ON,OFF", "SPI1:WRITE 123456,ON,OFF",
    "SPI0:READ? 1,aa,ON,OFf", "SPI0:READ? 10,bb,oN,OFF", "SPI0:READ? 100,gg,ON,OfF",
    "SPI1:READ? 1,aa,ON,OFf", "SPI1:READ? 10,bb,oN,OFF", "SPI1:READ? 100,gg,ON,OfF",
    "SPI0:READ? 1,00,ON,OFf", "SPI0:READ? 10,11,oN,OFF", "SPI0:READ? 100,99,ON,OfF",
    "SPI1:READ? 1,00,ON,OFf", "SPI0:READ? 10,11,oN,OFF", "SPI0:READ? 100,99,ON,OfF",
    "SPI0:TRANSfer 12345,ON,OFF", "SPI0:TRANSfer 123456,ON,OFF",
    "SPI1:TRANSfer 12345,ON,OFF", "SPI1:TRANSfer 123456,ON,OFF",

    "I2C0:WRITE 78,0001020f2a7981ff7828,0",
    "I2C0:WRITE 78,403031323334,1",

    "I2C1:MEMory:WRITE 78,00,01020f2a7981ff7828,1",
    "I2C1:MEMory:WRITE 78,40,b1b2b3b4b5,1",
]

if __name__ == '__main__':
    import pyvisa
    from halo import Halo


    def send_test():

        inst: pyvisa.resources.MessageBasedResource = pyvisa.ResourceManager().open_resource(
            "USB0::0x2E8A::0x0488::e66038b7138f6535::INSTR",
            chunk_size=128)
        inst.timeout = 200
        inst.write_termination = "\n"
        inst.read_termination = "\n"

        def flush_errors():
            try:
                while True:
                    print("flush_errors()", inst.read())
            except pyvisa.errors.VisaIOError:
                with Halo('VisaIOError'):
                    cnt = 0
                    while cnt < 256:
                        cnt += 1
                        inst.write("SYSTem:ERRor?")
                        time.sleep(0.3)
                        ret = inst.read().strip()
                        print(ret)
                        if ret == "0, 'No error'":
                            return

        print("*RST")
        inst.write("*RST")
        flush_errors()

        for command in scpi_commands:
            print("- - " * 5)
            print(command)
            time.sleep(0.5)
            inst.write(command)
            time.sleep(0.5)

            try:
                ret = ""
                if command.split(" ")[0].endswith("?"):
                    ret = inst.read().strip()
                    print(ret)
                else:
                    print("Write only command")
            except pyvisa.errors.VisaIOError:
                pass
            finally:
                flush_errors()
                continue

        print("- - " * 5)
        flush_errors()

        inst.close()


    send_test()
