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
MACHINE:FREQuency[?] num
PIN[6|7|14|15|20|21|22|25]:MODE[?] INput|OUTput|ODrain
PIN[6|7|14|15|20|21|22|25]:VALue[?] 0|1|OFF|ON
PIN[6|7|14|15|20|21|22|25]:ON
PIN[6|7|14|15|20|21|22|25]:OFF
PIN[6|7|14|15|20|21|22|25]:PWM:FREQuency[?] num
PIN[6|7|14|15|20|21|22|25]:PWM:DUTY[?] num
LED:ON
LED:OFF
LED:VALue[?] 0|1|OFF|ON
LED:PWM:STATe[?] 0|1|OFF|ON
LED:PWM:ENable
LED:PWM:DISable
LED:PWM:FREQuency[?] num
LED:PWM:DUTY[?] num
I2C[01]:SCAN?
I2C[01]:FREQuency[?] num
I2C[01]:ADDRess:BIT[?] 0|1|DEFault
I2C[01]:WRITE address,buffer,stop
I2C[01]:READ? address,length,stop
I2C[01]:MEMory:WRITE address,memaddress,buffer,addrsize
I2C[01]:MEMory:READ? address,memaddress,nbytes,addrsize
SPI[01]:CSEL:POLarity[?] 0/1
SPI[01]:MODE[?] 0/1/2/3
SPI[01]:FREQuency[?] num
SPI[01]:TRANSfer length,data
ADC[0123]:READ?
"""
import sys
import time

from port_config import port_name

scpi_commands = [
    "*IDN?",
    "MACHINE:FREQuency?",
    "MACHINE:FREQuency 250e6",

    "PIN6:MODE?", "PIN6:MODE INput", "PIN6:MODE OUTput", "PIN6:MODE ODrain", "PIN6:MODE PWM",
    "PIN7:MODE?", "PIN7:MODE INput", "PIN7:MODE OUTput", "PIN7:MODE ODrain", "PIN7:MODE PWM",
    "PIN14:MODE?", "PIN14:MODE INput", "PIN14:MODE OUTput", "PIN14:MODE ODrain", "PIN14:MODE PWM",
    "PIN15:MODE?", "PIN15:MODE INput", "PIN15:MODE OUTput", "PIN15:MODE ODrain", "PIN15:MODE PWM",
    "PIN20:MODE?", "PIN20:MODE INput", "PIN20:MODE OUTput", "PIN20:MODE ODrain", "PIN20:MODE PWM",
    "PIN21:MODE?", "PIN21:MODE INput", "PIN21:MODE OUTput", "PIN21:MODE ODrain", "PIN21:MODE PWM",
    "PIN22:MODE?", "PIN22:MODE INput", "PIN22:MODE OUTput", "PIN22:MODE ODrain", "PIN22:MODE PWM",
    "PIN25:MODE?", "PIN25:MODE INput", "PIN25:MODE OUTput", "PIN25:MODE ODrain", "PIN25:MODE PWM",

    "PIN6:VALue?", "PIN6:VALue 0", "PIN6:VALue 1", "PIN6:VALue OFF", "PIN6:VALue ON", "PIN6:OFF", "PIN6:ON",
    "PIN7:VALue?", "PIN7:VALue 0", "PIN7:VALue 1", "PIN7:VALue OFF", "PIN7:VALue ON", "PIN7:OFF", "PIN7:ON",
    "PIN14:VALue?", "PIN14:VALue 0", "PIN14:VALue 1", "PIN14:VALue OFF", "PIN14:VALue ON", "PIN14:OFF", "PIN14:ON",
    "PIN15:VALue?", "PIN15:VALue 0", "PIN15:VALue 1", "PIN15:VALue OFF", "PIN15:VALue ON", "PIN15:OFF", "PIN15:ON",
    "PIN20:VALue?", "PIN20:VALue 0", "PIN20:VALue 1", "PIN20:VALue OFF", "PIN20:VALue ON", "PIN20:OFF", "PIN20:ON",
    "PIN21:VALue?", "PIN21:VALue 0", "PIN21:VALue 1", "PIN21:VALue OFF", "PIN21:VALue ON", "PIN21:OFF", "PIN21:ON",
    "PIN22:VALue?", "PIN22:VALue 0", "PIN22:VALue 1", "PIN22:VALue OFF", "PIN22:VALue ON", "PIN22:OFF", "PIN22:ON",
    "PIN25:VALue?", "PIN25:VALue 0", "PIN25:VALue 1", "PIN25:VALue OFF", "PIN25:VALue ON", "PIN25:OFF", "PIN25:ON",

    "PIN6:PWM:FREQuency?", "PIN6:PWM:FREQuency 12345", "PIN6:PWM:DUTY 12345", "PIN6:PWM:DUTY?",
    "PIN7:PWM:FREQuency?", "PIN7:PWM:FREQuency 12345", "PIN7:PWM:DUTY 12345", "PIN7:PWM:DUTY?",
    "PIN14:PWM:FREQuency?", "PIN14:PWM:FREQuency 12345", "PIN14:PWM:DUTY 12345", "PIN14:PWM:DUTY?",
    "PIN15:PWM:FREQuency?", "PIN15:PWM:FREQuency 12345", "PIN15:PWM:DUTY 12345", "PIN15:PWM:DUTY?",
    "PIN20:PWM:FREQuency?", "PIN20:PWM:FREQuency 12345", "PIN20:PWM:DUTY 12345", "PIN20:PWM:DUTY?",
    "PIN21:PWM:FREQuency?", "PIN21:PWM:FREQuency 12345", "PIN21:PWM:DUTY 12345", "PIN21:PWM:DUTY?",
    "PIN22:PWM:FREQuency?", "PIN22:PWM:FREQuency 12345", "PIN22:PWM:DUTY 12345", "PIN22:PWM:DUTY?",
    "PIN25:PWM:FREQuency?", "PIN25:PWM:FREQuency 12345", "PIN25:PWM:DUTY 12345", "PIN25:PWM:DUTY?",

    "LED:VALue OFF", "LED:VALue ON", "LED:OFF", "LED:ON",
    "LED:PWM:FREQuency 12345", "LED:PWM:FREQuency?", "LED:PWM:DUTY?", "LED:PWM:DUTY 12345",

    "ADC0:READ?", "ADC1:READ?", "ADC2:READ?", "ADC3:READ?",

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
    "SPI0:WRITE 12345", "SPI0:WRITE 123456",
    "SPI1:WRITE 12345", "SPI1:WRITE 123456",
    "SPI0:READ? 1,aa", "SPI0:READ? 10,bb", "SPI0:READ? 100,gg",
    "SPI1:READ? 1,aa", "SPI1:READ? 10,bb", "SPI1:READ? 100,gg",
    "SPI0:READ? 1,00", "SPI0:READ? 10,11", "SPI0:READ? 100,99",
    "SPI1:READ? 1,00", "SPI0:READ? 10,11", "SPI0:READ? 100,99",
    "SPI0:TRANSfer 12345", "SPI0:TRANSfer 123456",
    "SPI1:TRANSfer 12345", "SPI1:TRANSfer 123456",

    "I2C0:WRITE 78,0001020f2a7981ff7828,0",
    "I2C0:WRITE 78,403031323334,1",

    "I2C1:MEMory:WRITE 78,00,01020f2a7981ff7828,1",
    "I2C1:MEMory:WRITE 78,40,b1b2b3b4b5,1",
]

if __name__ == '__main__':
    import pyvisa
    from halo import Halo


    def send_test():

        rm = pyvisa.ResourceManager("@py")

        print(rm.list_resources())

        # inst = rm.open_resource(port_name)
        inst = pyvisa.resources.SerialInstrument(rm, port_name)
        inst.open()

        with Halo("*RST"):
            inst.write("*RST")
            time.sleep(0.5)
            while inst.bytes_in_buffer > 0:
                time.sleep(0.01)
                ret = inst.read().strip()
                print(ret)

        time.sleep(0.5)
        for command in scpi_commands:
            print("- - " * 5)
            print(command)
            inst.write(command)
            time.sleep(0.3)
            if inst.bytes_in_buffer > 0:
                ret = inst.read().strip()
                print(ret)

            while inst.bytes_in_buffer > 0:
                time.sleep(0.01)
                ret = inst.read().strip()
                print(ret)

        inst.close()


    send_test()
