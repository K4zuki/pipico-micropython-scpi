import io
import struct
from MicroScpiDevice import MicroScpiDevice
from tmc import TmcBulkInOutMessage
from usb488 import Usb488Interface


class Usb488ScpiPico(Usb488Interface):
    def __init__(self, parser: MicroScpiDevice):
        super().__init__()
        self.parser = parser

    def on_device_dependent_out(self) -> None:
        """ Action on Bulk out transfer with megID==DEV_DEP_MSG_OUT.
        Subclasses must override this method.
        """
        """ Table 3 -- Example *IDN? Bulk-OUT USBTMC device dependent command message
                    |Offset |Field                      |Size   |Value                  |Description
        ------------------------------------------------------------------------------------------------------------------------
        Bulk-OUT    |0      |MsgID                      |1      |DEV_DEP_MSG_OUT        |See the USBTMC specification,
        Header      |1      |bTag                       |1      |0x01 (varies with each |Table 1.
                    |       |                           |       |transfer)              |
                    |2      |bTagInverse                |1      |0xFE                   |
                    |3      |Reserved                   |1      |0x00                   |
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |4      |TransferSize               |4      |0x06                   |Command specific content.
        device      |5      |                           |       |0x00                   |See the USBTMC specification,
        dependent   |6      |                           |       |0x00                   |Table 3.
        command     |7      |                           |       |0x00                   |
        message     |8      |bmTransfer                 |1      |0x01 (EOM is set).     |
                    |       |Attributes                 |       |                       |
                    |9      |Reserved                   |1      |0x00                   |
                    |10     |Reserved                   |1      |0x00                   |
                    |11     |Reserved                   |1      |0x00                   |
                    |12     |Device dependent           |1      |0x2A = ‘*’             |USBTMC message data byte 0.
                    |13     |message data bytes         |1      |0x49 = ‘I’             |USBTMC message data byte 1.
                    |14     |                           |1      |0x44 = ‘D’             |USBTMC message data byte 2.
                    |15     |                           |1      |0x4E = ‘N’             |USBTMC message data byte 3.
                    |16     |                           |1      |0x3F = ‘?’             |USBTMC message data byte 4.
                    |17     |                           |1      |0x0A = ‘\n’ = newline  |USBTMC message data byte 5.
        ------------------------------------------------------------------------------------------------------------------------
                    |18-19  |Alignment bytes            |2      |0x0000                 |Two alignment bytes are added
                    |       |(required to make the      |       |(not required to be    |to bring the number of DATA
                    |       |number of bytes in the     |       |0x0000)                |bytes in the transaction to 20,
                    |       |transaction a multiple of  |       |                       |which is divisible by 4.
                    |       |4)                         |       |                       |
    
        """
        transfer_size, attribute = struct.unpack_from("<IB3x", self.last_bulkout_msg.tmc_specific, 0)

        message: str = self.last_bulkout_msg.message.decode("utf-8")
        response = b""
        with io.StringIO() as sio:
            self.parser.stdout = sio
            for line in message.split(";"):
                self.parser.parse_and_process(line)
            response = sio.getvalue().encode("utf8")
        print(response)
        self.last_bulkout_msg = TmcBulkInOutMessage(self.last_bulkout_msg.msg_id, self.last_bulkout_msg.b_tag,
                                                    self.last_bulkout_msg.tmc_specific,
                                                    self.last_bulkout_msg.message, response)

        self.dev_dep_out_messages.append(self.last_bulkout_msg)
