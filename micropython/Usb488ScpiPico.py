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

        message: str = io.StringIO(self.last_bulkout_msg.message.decode("utf-8")).readline()
        response = b""
        with io.StringIO() as sio:
            self.parser.stdout = sio
            for line in message.split(";"):
                self.parser.parse_and_process(line)
            response = sio.getvalue().encode("utf8")
            sio.flush()
        response.replace(b"\n", b";")

        self.last_bulkout_msg = TmcBulkInOutMessage(self.last_bulkout_msg.msg_id, self.last_bulkout_msg.b_tag,
                                                    self.last_bulkout_msg.tmc_specific,
                                                    self.last_bulkout_msg.message, response)
        print(response)

        self.dev_dep_out_messages.append(self.last_bulkout_msg)

    def on_request_device_dependent_in(self) -> None:
        """ Action on Bulk out transfer with megID==DEV_DEP_MSG_IN.
        Subclasses must override this method.
        """
        """Table 5 -- Bulk-IN example, 488.2 compliant response USBTMC message
                    |Offset |Field              |Size   |Value                          |Description
        ------------------------------------------------------------------------------------------------------------------------
        Bulk-IN     |0      |MsgID              |1      |DEV_DEP_MSG_IN                 |See the USBTMC specification, Table
        Header      |1      |bTag               |1      |0x02 (matches bTag in          |8.
                    |       |                   |       |REQUEST_DEV_DEP_               |
                    |       |                   |       |MSG_IN)                        |
                    |2      |bTagInverse        |1      |0xFD                           |
                    |3      |Reserved           |1      |0x00                           |
                    |4      |TransferSize       |4      |0x17                           |USBTMC response specific content.
                    |5      |                   |       |0x00                           |See the USBTMC specification, Table
                    |6      |                   |       |0x00                           |9.
                    |7      |                   |       |0x00                           |
                    |8      |bmTransfer         |1      |0x01 (EOM=1)                   |
                    |       |Attributes         |       |                               |
                    |9      |Reserved           |1      |0x00                           |
                    |10     |Reserved           |1      |0x00                           |
                    |11     |Reserved           |1      |0x00                           |
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |12     |Device dependent   |1      |0x58 = ‘X’                     |USBTMC message data byte 0.
        device      |13     |                   |1      |0x59 = ‘Y’                     |USBTMC message data byte 1.
        dependent   |14     |                   |1      |0x5A = ‘Z’                     |USBTMC message data byte 2.
        message     |15     |                   |1      |0x43 = ‘C ‘                    |USBTMC message data byte 3.
                    |16     |                   |1      |0x4F = ‘O’                     |USBTMC message data byte 4.
                    |17     |                   |1      |0x2C = ‘,’                     |USBTMC message data byte 5.
                    |18     |                   |1      |0x32 = ‘2’                     |USBTMC message data byte 6.
                    |19     |                   |1      |0x34 = ‘4’                     |USBTMC message data byte 7.
                    |20     |                   |1      |0x36 = ‘6’                     |USBTMC message data byte 8.
                    |21     |                   |1      |0x42 = ‘B’                     |USBTMC message data byte 9.
                    |22     |                   |1      |0x2C = ‘,’                     |USBTMC message data byte 10.
                    |23     |                   |1      |0x53 = ‘S’                     |USBTMC message data byte 11.
                    |24     |                   |1      |0x2D = ‘-‘                     |USBTMC message data byte 12.
                    |25     |                   |1      |0x30 = ‘0’                     |USBTMC message data byte 13.
                    |26     |                   |1      |0x31 = ‘1’                     |USBTMC message data byte 14.
                    |27     |                   |1      |0x32 = ‘2’                     |USBTMC message data byte 15.
                    |28     |                   |1      |0x33 = ‘3’                     |USBTMC message data byte 16.
                    |29     |                   |1      |0x2D = ‘-‘                     |USBTMC message data byte 17.
                    |30     |                   |1      |0x30 = ‘0’                     |USBTMC message data byte 18.
                    |31     |                   |1      |0x32 = ‘2’                     |USBTMC message data byte 19.
                    |32     |                   |1      |0x2C = ‘,’                     |USBTMC message data byte 20.
                    |33     |                   |1      |0x30 = ‘0’                     |USBTMC message data byte 21.
                    |34     |                   |1      |0x0A = ‘\n’ = newline          |USBTMC message data byte 22.
                    |35     |Alignment byte     |1      |0x00 (not required to be       |Alignment byte.
                    |       |                   |       |0x00)                          |
        """
        self._bulkout_header_processed = False
        transfer_size, attribute, termchar = struct.unpack_from("<IBB2x", self.last_bulkout_msg.tmc_specific, 0)
        print("on_request_device_dependent_in")

        header: Descriptor = self.draft_device_dependent_in_header(self.last_bulkout_msg.b_tag, transfer_size)
        if len(self.dev_dep_out_messages) > 0:
            message: TmcBulkInOutMessage = self.dev_dep_out_messages.popleft()
            print(message)
            print("response message:", message.response)
            if len(message.response) > 0:
                # There is query response
                self.send_device_dependent_in(header, message.response)
            else:
                print("no response")
        else:
            print("No response stock left")
