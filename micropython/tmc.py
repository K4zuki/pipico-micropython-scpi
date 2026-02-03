# MicroPython USB TMC module
#
# Test and Measurement Class
#
# MIT license; Copyright (c) 2025 Kazuki Yamamoto

from micropython import const, schedule
import io
import machine
from collections import deque, namedtuple
import struct
import time

from usb.device.core import Interface, Descriptor, split_bmRequestType, Buffer

_EP_IN_FLAG = const(1 << 7)

# Control transfer stages
_STAGE_IDLE = const(0)
_STAGE_SETUP = const(1)
_STAGE_DATA = const(2)
_STAGE_ACK = const(3)

"""
5.5 Interface Descriptor

Table 43 -- Interface Descriptor
------------------------------------------------------------------------------------------------------------------------
|Offset |Field              |Size   |Value          |Description
------------------------------------------------------------------------------------------------------------------------
|0      |bLength            |1      |0x09           |Size of this descriptor in bytes.
|1      |bDescriptorType    |1      |0x04           |INTERFACE Descriptor Type. See USB 2.0
|       |                   |       |               |specification, Table 9-5.
|2      |bInterfaceNumber   |1      |Number         |Number of this interface. Zero-based value
|       |                   |       |               |identifying the index in the array of concurrent
|       |                   |       |               |interfaces supported by this configuration.
|3      |bAlternateSetting  |1      |0x00           |Value used to select this alternate setting for the
|       |                   |       |               |interface identified in the prior field.
|4      |bNumEndpoints      |1      |Number         |Number of endpoints used by this interface
|       |                   |       |               |(excluding endpoint zero). If this value is zero, this
|       |                   |       |               |interface only uses the Default Control Pipe.
|5      |bInterfaceClass    |1      |Class = 0xFE   |“Application-Class” class code, assigned by USB-IF.
|       |                   |       |               |The Host must not load a USBTMC driver based on
|       |                   |       |               |just the bInterfaceClass field.
|6      |bInterfaceSubClass |1      |0x03           |Subclass code, assigned by USB-IF.
|7      |bInterfaceProtocol |1      |Protocol       |Protocol code. See Table 44.
|8      |iInterface         |1      |Index          |Index of string descriptor describing this interface.
------------------------------------------------------------------------------------------------------------------------
"""
_INTERFACE_CLASS_TMC = const(0xFE)
_INTERFACE_SUBCLASS_TMC = const(0x03)

"""
Table 44 -- USBTMC bInterfaceProtocol values
------------------------------------------------------------------------------------------------------------------------
|bInterfaceProtocol Value   |Description
------------------------------------------------------------------------------------------------------------------------
|0                          |USBTMC interface. No subclass specification applies.
|1                          |USBTMC USB488 interface. See the USB488 subclass specification.
|2-127                      |Reserved
------------------------------------------------------------------------------------------------------------------------
"""
_PROTOCOL_NONE = const(0x00)
_PROTOCOL_488 = const(0x01)

"""
4.2 USBTMC class specific requests
All USBTMC class specific requests must be sent with a Setup packet as shown below in Table 14.

Table 14 -- USBTMC class specific request format
------------------------------------------------------------------------------------------------------------------------
|Offset |Field          |Size   |Value      |Description
------------------------------------------------------------------------------------------------------------------------
|0      |bmRequestType  |1      |Bitmap     |D7         Data transfer direction 0 - Host-to-device
|       |               |       |           |                                   1 - Device-to-host
|       |               |       |           |           Varies according to request.
|       |               |       |           |D6...D5    Type                    0 - Standard
|       |               |       |           |                                   1 - Class
|       |               |       |           |                                   2 - Vendor
|       |               |       |           |                                   3 - Reserved
|       |               |       |           |           Type = Class for all control endpoint requests
|       |               |       |           |           specified in this USBTMC specification and for all
|       |               |       |           |           control endpoint requests specified in USBTMC
|       |               |       |           |           subclass specifications.
|       |               |       |           |D4...D0    Recipient               0 - Device
|       |               |       |           |                                   1 - Interface
|       |               |       |           |                                   2 - Endpoint
|       |               |       |           |                                   3 - Other
|       |               |       |           |                                   4 – 31 - Reserved
|       |               |       |           |           Varies according to request.
|1      |bRequest       |1      |Value      |If bmRequestType.Type = Class, see section 4.2.1
|2      |wValue         |2      |Value      |Word sized field that varies according to request. See the USB 2.0
|       |               |       |           |specification, section 9.3.3.
|4      |wIndex         |2      |Index      |Word sized field that varies according to request, typically used to pass
|       |               |       |or Offset  |an index or offset. See the USB 2.0 specification, section 9.3.4.
|6      |wLength        |2      |Count      |Number of bytes to transfer if there is a Data stage. See the USB 2.0
|       |               |       |           |specification, section 9.3.5. Varies according to request.
------------------------------------------------------------------------------------------------------------------------
"""
_REQ_TYPE_STANDARD = const(0x0)
_REQ_TYPE_CLASS = const(0x1)
_REQ_TYPE_VENDOR = const(0x2)
_REQ_TYPE_RESERVED = const(0x3)

# Standard control request bmRequest fields, can extract by calling split_bmRequestType()
_REQ_RECIPIENT_DEVICE = const(0x0)
_REQ_RECIPIENT_INTERFACE = const(0x1)
_REQ_RECIPIENT_ENDPOINT = const(0x2)
_REQ_RECIPIENT_OTHER = const(0x3)

"""
If bmRequestType.Type = Class

4.2.1 USBTMC requests
Table 15 below shows the USBTMC specific requests.

Table 15 -- USBTMC bRequest values
------------------------------------------------------------------------------------------------------------------------
|bRequest   |Name                           |Required/Optional  |Comment
------------------------------------------------------------------------------------------------------------------------
|0          |Reserved                       |Reserved           |Reserved.
|1          |INITIATE_ABORT_BULK_OUT        |Required           |Aborts a Bulk-OUT transfer.
|2          |CHECK_ABORT_BULK_OUT_STATUS    |Required           |Returns the status of the previously sent 
|           |                               |                   |INITIATE_ABORT_BULK_OUT request.
|3          |INITIATE_ABORT_BULK_IN         |Required           |Aborts a Bulk-IN transfer.
|4          |CHECK_ABORT_BULK_IN_STATUS     |Required           |Returns the status of the previously sent 
|           |                               |                   |INITIATE_ABORT_BULK_IN request.
|5          |INITIATE_CLEAR                 |Required           |Clears all previously sent pending and unprocessed 
|           |                               |                   |Bulk-OUT USBTMC message content and clears all 
|           |                               |                   |pending Bulk-IN transfers from the USBTMC interface.
|6          |CHECK_CLEAR_STATUS             |Required           |Returns the status of the previously sent 
|           |                               |                   |INITIATE_CLEAR request.
|7          |GET_CAPABILITIES               |Required           |Returns attributes and capabilities of the 
|           |                               |                   |USBTMC interface.
|8-63       |Reserved                       |Reserved           |Reserved for use by the USBTMC specification.
|64         |INDICATOR_PULSE                |Optional           |A mechanism to turn on an activity indicator 
|           |                               |                   |for identification purposes. The device indicates 
|           |                               |                   |whether or not it supports this request in 
|           |                               |                   |the GET_CAPABILITIES response packet.
|65-127     |Reserved                       |Reserved           |Reserved for use by the USBTMC specification.
|128-191    |Reserved                       |Reserved           |Reserved for use by USBTMC subclass specifications.
|192-255    |Reserved                       |Reserved           |Reserved for use by the VISA specification
------------------------------------------------------------------------------------------------------------------------
"""
# USBTMC bRequest values
_REQ_INITIATE_ABORT_BULK_OUT = const(1)  # 0xA2 (Dir = IN, Type = Class, Recipient = Endpoint)
_REQ_CHECK_ABORT_BULK_OUT_STATUS = const(2)  # 0xA2 (Dir = IN, Type = Class, Recipient = Endpoint)
_REQ_INITIATE_ABORT_BULK_IN = const(3)  # 0xA2 (Dir = IN, Type = Class, Recipient = Endpoint)
_REQ_CHECK_ABORT_BULK_IN_STATUS = const(4)  # 0xA2 (Dir = IN, Type = Class, Recipient = Endpoint)
_REQ_INITIATE_CLEAR = const(5)  # 0xA1 (Dir = IN, Type = Class, Recipient = Interface)
_REQ_CHECK_CLEAR_STATUS = const(6)  # 0xA1 (Dir = IN, Type = Class, Recipient = Interface)
_REQ_GET_CAPABILITIES = const(7)  # 0xA1 (Dir = IN, Type = Class, Recipient = Interface)
_REQ_INDICATOR_PULSE = const(64)  # 0xA1 (Dir = IN, Type = Class, Recipient = Interface)

"""
Table 16 -- USBTMC_status values
------------------------------------------------------------------------------------------------------------------------
|USBTMC_status  |MACRO                              |Recommended    |Description
|               |                                   |interpretation |
|               |                                   |by Host        |
|               |                                   |software       |
------------------------------------------------------------------------------------------------------------------------
|0x00           |Reserved                           |Reserved       |Reserved
|0x01           |STATUS_SUCCESS                     |Success        |Success
|0x02           |STATUS_PENDING                     |Warning        |This status is valid if a device has received a
|               |                                   |               |USBTMC split transaction CHECK_STATUS
|               |                                   |               |request and the request is still being processed.
|               |                                   |               |See 4.2.1.1.
|0x03-0x1F      |Reserved                           |Warning        |Reserved for USBTMC use.
|0x20-0x3F      |Reserved                           |Warning        |Reserved for subclass use.
|0x40-0x7F      |Reserved                           |Warning        |Reserved for VISA use.
|0x80           |STATUS_FAILED                      |Failure        |Failure, unspecified reason, and a more specific
|               |                                   |               |USBTMC_status is not defined.
|0x81           |STATUS_TRANSFER_NOT_IN_PROGRESS    |               |This status is only valid if a device has received
|               |                                   |               |an INITIATE_ABORT_BULK_OUT or
|               |                                   |               |INITIATE_ABORT_BULK_IN request and the
|               |                                   |               |specified transfer to abort is not in progress.
|0x82           |STATUS_SPLIT_NOT_|IN_PROGRESS      |               |Failure This status is valid if the device received a
|                                                   |               |CHECK_STATUS request and the device is not
|               |                                   |               |processing an INITIATE request.
|0x83           |STATUS_SPLIT_IN_PROGRESS           |Failure        |This status is valid if the device received a new
|               |                                   |               |class-specific request and the device is still
|               |                                   |               |processing an INITIATE.
|0x84-0x9F      |Reserved                           |Failure        |Reserved for USBTMC use.
|0xA0-0xBF      |Reserved                           |Failure        |Reserved for subclass use.
|0xC0-0xFF      |Reserved                           |Failure        |Reserved for VISA use.
------------------------------------------------------------------------------------------------------------------------
"""
_TMC_STATUS_SUCCESS = const(0x01)
_TMC_STATUS_PENDING = const(0x02)
_TMC_STATUS_FAILED = const(0x80)
_TMC_STATUS_TRANSFER_NOT_IN_PROGRESS = const(0x81)
_TMC_STATUS_SPLIT_NOT_IN_PROGRESS = const(0x82)
_TMC_STATUS_SPLIT_IN_PROGRESS = const(0x83)

"""
Table 37 -- GET_CAPABILITIES response format
------------------------------------------------------------------------------------------------------------------------
|Offset         |Field          |Size   |Value      |Description
------------------------------------------------------------------------------------------------------------------------
|0              |USBTMC_status  |1      |Value      |Status indication for this request. See Table 16.
|1              |Reserved       |1      |0x00       |Reserved. Must be 0x00.
|2              |bcdUSBTMC      |2      |BCD        |BCD version number of the relevant USBTMC specification for
|               |               |       |(0x0100 or |this USBTMC interface. Format is as specified for bcdUSB in the
|               |               |       |greater)   |USB 2.0 specification, section 9.6.1.
|4              |USBTMC         |1      |Bitmap     |D7...D3    |Reserved. All bits must be 0.
|               |Interface      |       |           |D2         |1 – The USBTMC interface accepts the
|               |Capabilities   |       |           |           |INDICATOR_PULSE request.
|               |               |       |           |           |0 – The USBTMC interface does not accept the
|               |               |       |           |           |INDICATOR_PULSE request. The device, when
|               |               |       |           |           |an INDICATOR_PULSE request is received,
|               |               |       |           |           |must treat this command as a non-defined
|               |               |       |           |           |command and return a STALL handshake
|               |               |       |           |           |packet.
|               |               |       |           |D1         |1 – The USBTMC interface is talk-only.
|               |               |       |           |           |0 – The USBTMC interface is not talk-only.
|               |               |       |           |D0         |1 – The USBTMC interface is listen-only.
|               |               |       |           |           |0 – The USBTMC interface is not listen-only.
|5              |USBTMC         |1      |Bitmap     |D7...D1    |Reserved. All bits must be 0.
|               |Device         |       |           |D0         |1 – The device supports ending a Bulk-IN transfer
|               |Capabilities   |       |           |           |from this USBTMC interface when a byte
|               |               |       |           |           |matches a specified TermChar.
|               |               |       |           |           |0 – The device does not support ending a Bulk-IN
|               |               |       |           |           |transfer from this USBTMC interface when a
|               |               |       |           |           |byte matches a specified TermChar.
|6              |Reserved       |6      |All bytes  |Reserved for USBTMC use. All bytes must be 0x00.
|               |               |       |must be    |
|               |               |       |0x00.      |
|12             |Reserved       |12     |Reserved   |Reserved for USBTMC subclass use. If no subclass specification
|               |               |       |           |applies, all bytes must be 0x00.
------------------------------------------------------------------------------------------------------------------------
"""
_bcdUSBTMC = const(0x0100)

"""
3.2 Bulk-OUT endpoint
The Host uses the Bulk-OUT endpoint to send USBTMC command messages to the device. For all Bulk-
OUT USBTMC command messages, whether defined in this specification, a USBTMC subclass
specification, or some other specification, the Host must begin the first USB transaction in each Bulk-OUT
transfer of command message content with a Bulk-OUT Header. The Bulk-OUT Header is defined below
in Table 1.

Table 1 -- USBTMC message Bulk-OUT Header
------------------------------------------------------------------------------------------------------------------------
|Offset |Field              |Size   |Value              |Description
------------------------------------------------------------------------------------------------------------------------
|0      |MsgID              |1      |Value              |Specifies the USBTMC message and the type of the
|       |                   |       |                   |USBTMC message. See Table 2.
|1      |bTag               |1      |Value              |A transfer identifier. The Host must set bTag
|       |                   |       |                   |different than the bTag used in the previous Bulk-
|       |                   |       |                   |OUT Header. The Host should increment the bTag
|       |                   |       |                   |by 1 each time it sends a new Bulk-OUT Header.
|       |                   |       |                   |The Host must set bTag such that 1<=bTag<=255.
|2      |bTagInverse        |1      |Value              |The inverse (one’s complement) of the bTag. For
|       |                   |       |                   |example, the bTagInverse of 0x5B is 0xA4.
|3      |Reserved           |1      |0x00               |Reserved. Must be 0x00.
|4-11   |USBTMC command     |8      |USBTMC command     |USBTMC command message specific. See section
|       |message specific   |       |message specific   |3.2.1.
------------------------------------------------------------------------------------------------------------------------

Table 2 -- MsgID values
------------------------------------------------------------------------------------------------------------------------
|MsgID      |Direction                  |MACRO                      |Description
|           |OUT=Host-to-device         |                           |
|           |IN=Device-to-Host          |                           |
------------------------------------------------------------------------------------------------------------------------
|0          |Reserved                   |Reserved                   |Reserved
|1          |OUT                        |DEV_DEP_MSG_OUT            |The USBTMC message is a USBTMC device dependent
|           |                           |                           |command message. See section 3.2.1.1.
|           |IN                         |(no defined response)      |There is no defined response for this USBTMC command
|           |                           |                           |message.
|2          |OUT                        |REQUEST_DEV_DEP_MSG_IN     |The USBTMC message is a USBTMC command message
|           |                           |                           |that requests the device to send a USBTMC response
|           |                           |                           |message on the Bulk-IN endpoint. See section 3.2.1.2.
|           |IN                         |DEV_DEP_MSG_IN             |The USBTMC message is a USBTMC response message to
|           |                           |                           |the REQUEST_DEV_DEP_MSG_IN. See section 3.3.1.1.
|3-125      |Reserved                   |Reserved                   |Reserved for USBTMC use.
|126        |OUT                        |VENDOR_SPECIFIC_OUT        |The USBTMC message is a USBTMC vendor specific
|           |                           |                           |command message. See section 3.2.1.3.
|           |IN                         |(no defined response)      |There is no defined response for this USBTMC command
|           |                           |                           |message.
|127        |OUT                        |REQUEST_VENDOR_SPECIFIC_IN |The USBTMC message is a USBTMC command message
|           |                           |                           |that requests the device to send a vendor specific USBTMC
|           |                           |                           |response message on the Bulk-IN endpoint. See section
|           |                           |                           |3.2.1.4
|           |IN                         |VENDOR_SPECIFIC_IN         |The USBTMC message is a USBTMC response message to
|           |                           |                           |the REQUEST_VENDOR_SPECIFIC_IN. See section
|           |                           |                           |3.3.1.2.
|128-191    |Reserved                   |Reserved                   |Reserved for USBTMC subclass use.
|192-255    |Reserved                   |Reserved                   |Reserved for VISA specification use.
------------------------------------------------------------------------------------------------------------------------
"""
_BULK_OUT_HEADER_SIZE = const(12)
_MSGID_DEV_DEP_MSG_OUT = const(1)
_MSGID_REQUEST_DEV_DEP_MSG_IN = const(2)
_MSGID_DEV_DEP_MSG_IN = const(2)
_MSGID_VENDOR_SPECIFIC_OUT = const(126)
_MSGID_REQUEST_VENDOR_SPECIFIC_IN = const(127)
_MSGID_VENDOR_SPECIFIC_IN = const(127)

_wMaxPacketSize = const(64)
_BULK_IN_HEADER_SIZE = const(12)
_HEADERS_BASE_SIZE = const(4)


class TmcBulkInOutMessage(namedtuple("TmcBulkInOutMessage",
                                     [
                                         "msg_id",  # msgID
                                         "b_tag",  # bTag
                                         "tmc_specific",  # USBTMC command message specific
                                         "message",  # payload message from host
                                         "response"  # response message to host
                                     ])):
    """
    * ``msg_id``: msgID
    * ``b_tag``:  bTag
    * ``tmc_specific``:  USBTMC command message specific
    * ``message``: payload message from host
    * ``response``: response message to host
    """


class TMCInterface(Interface):
    last_bulkout_msg: TmcBulkInOutMessage

    def __init__(self,
                 protocol=_PROTOCOL_NONE,
                 interface_str=None,
                 interrupt_ep=False,
                 talk_only=False,
                 listen_only=False,
                 indicator_pulse=False,
                 termchar=False
                 ):
        super().__init__()
        self.ep_out = None  # Set during enumeration. RX direction (host to device)
        self.ep_in = None  # TX direction (device to host)
        self.ep_int = None  # set during enumeration
        self._rx = Buffer(256)
        self._tx = Buffer(256)

        self.protocol = protocol
        self.interface_str = interface_str
        self.interrupt_ep = interrupt_ep
        self.indicator_pulse = indicator_pulse
        self.talk_only = talk_only
        self.listen_only = listen_only
        self.termchar = termchar
        self.capabilities = self.get_capabilities()

        self.dev_dep_out_messages = deque([], 16)
        self._bulkout_header_processed = False

    def desc_cfg(self, desc, itf_num, ep_num, strs):
        # Function to build configuration descriptor contents for this interface
        # or group of interfaces. This is called on each interface from
        # USBDevice.init().
        #
        # This function should insert:
        #
        # - At least one standard Interface descriptor (can call
        # - desc.interface()).
        desc.interface(itf_num,
                       self.num_eps(),
                       _INTERFACE_CLASS_TMC,
                       _INTERFACE_SUBCLASS_TMC,
                       self.protocol,
                       len(strs) if self.interface_str else 0
                       )

        if self.interface_str:
            strs.append(self.interface_str)

        # Plus, optionally:
        #
        # - One or more endpoint descriptors (can call desc.endpoint()).
        # - An Interface Association Descriptor, prepended before.
        # - Other class-specific configuration descriptor data.
        #
        self.ep_out = ep_num
        desc.endpoint(self.ep_out, "bulk", _wMaxPacketSize)
        self.ep_in = ep_num | _EP_IN_FLAG
        desc.endpoint(self.ep_in, "bulk", _wMaxPacketSize)

        if self.interrupt_ep:
            self.ep_int = (ep_num + 1) | _EP_IN_FLAG
            desc.endpoint(self.ep_int, "interrupt", 8, 8)

        # This function is called twice per call to USBDevice.init(). The first
        # time the values of all arguments are dummies that are used only to
        # calculate the total length of the descriptor. Therefore, anything this
        # function does should be idempotent and it should add the same
        # descriptors each time. If saving interface numbers or endpoint numbers
        # for later
        #
        # Parameters:
        #
        # - desc - Descriptor helper to write the configuration descriptor bytes into.
        #   The first time this function is called 'desc' is a dummy object
        #   with no backing buffer (exists to count the number of bytes needed).
        #
        # - itf_num - First bNumInterfaces value to assign. The descriptor
        #   should contain the same number of interfaces returned by num_itfs(),
        #   starting from this value.
        #
        # - ep_num - Address of the first available endpoint number to use for
        #   endpoint descriptor addresses. Subclasses should save the
        #   endpoint addresses selected, to look up later (although note the first
        #   time this function is called, the values will be dummies.)
        #
        # - strs - list of string descriptors for this USB device. This function
        #   can append to this list, and then insert the index of the new string
        #   in the list into the configuration descriptor.

    def num_eps(self):
        # Return the number of USB Endpoint numbers represented by this object
        # (as set in desc_cfg().)
        #
        # Note for each count returned by this function, the interface may
        # choose to have both an IN and OUT endpoint (i.e. IN flag is not
        # considered a value here.)
        #
        # This value can be zero, if the USB Host only communicates with this
        # interface using control transfers.
        """
        A USBTMC interface with a bInterfaceProtocol = 0x00 must have exactly one Bulk-OUT endpoint, exactly
        one Bulk-IN endpoint, and may have at most one Interrupt-IN endpoint. Additional endpoints must be
        placed in another interface.
        """
        # 1x Bulk IN|OUT + ~1x Interrupt IN
        return 1 + (1 if self.interrupt_ep else 0)

    def on_device_control_xfer(self, stage, request):
        # Control transfer callback. Override to handle a non-standard device
        # control transfer where bmRequestType Recipient is Device, Type is
        # utils.REQ_TYPE_CLASS, and the lower byte of wIndex indicates this interface.
        #
        # (See USB 2.0 specification 9.4 Standard Device Requests, p250).
        #
        # This particular request type seems pretty uncommon for a device class
        # driver to need to handle, most hosts will not send this so most
        # implementations won't need to override it.
        #
        # Parameters:
        #
        # - stage is one of utils.STAGE_SETUP, utils.STAGE_DATA, utils.STAGE_ACK.
        #
        # - request is a memoryview into a USB request packet, as per USB 2.0
        #   specification 9.3 USB Device Requests, p250.  the memoryview is only
        #   valid while the callback is running.
        #
        # The function can call split_bmRequestType(request[0]) to split
        # bmRequestType into (Recipient, Type, Direction).
        #
        # Result, any of:
        #
        # - True to continue the request, False to STALL the endpoint.
        # - Buffer interface object to provide a buffer to the host as part of the
        #   transfer, if applicable.
        return False

    def on_interface_control_xfer(self, stage, request):
        # Control transfer callback. Override to handle a device control
        # transfer where bmRequestType Recipient is Interface, and the lower byte
        # of wIndex indicates this interface.
        #
        # (See USB 2.0 specification 9.4 Standard Device Requests, p250).
        #
        # bmRequestType Type field may have different values. It's not necessary
        # to handle the mandatory Standard requests (bmRequestType Type ==
        # utils.REQ_TYPE_STANDARD), if the driver returns False in these cases then
        # TinyUSB will provide the necessary responses.
        #
        # See on_device_control_xfer() for a description of the arguments and
        # possible return values.

        # Handle standard and class-specific interface control transfers
        bmRequestType, bRequest, wValue, wIndex, wLength = struct.unpack("BBHHH", request)

        recipient, req_type, data_direction = split_bmRequestType(bmRequestType)
        resp = Descriptor(bytearray(1))
        resp.pack("B", _TMC_STATUS_SUCCESS)

        if stage == _STAGE_SETUP:
            if req_type == _REQ_TYPE_STANDARD:
                return False  # Let tinyUSB work
            elif req_type == _REQ_TYPE_CLASS:
                if bRequest == _REQ_INITIATE_CLEAR:
                    """ Table 30 -- INITIATE_CLEAR Setup packet
                    bmRequestType   |0xA1 (Dir = IN, Type = Class, Recipient = Interface)
                    bRequest        |INITIATE_CLEAR, see Table 15.
                    wValue          |0x0000
                    wIndex          |Must specify interface number per the USB 2.0 specification, section 9.3.4.
                    wLength         |0x0001. Number of bytes to transfer per the USB 2.0 specification, section 9.3.5.
                    """
                    """ Table 31 -- INITIATE_CLEAR response format
                    Offset  |Field          |Size   |Value  |Description
                    ------------------------------------------------------------------------------------------------------------------------
                    0       |USBTMC_status  |1      |Value  |Status indication for this request. See Table 32.
                    """
                    return resp.b
                elif bRequest == _REQ_CHECK_CLEAR_STATUS:
                    """ Table 33 -- CHECK_CLEAR_STATUS Setup packet
                    bmRequestType   |0xA1 (Dir = IN, Type = Class, Recipient = Interface)
                    bRequest        |CHECK_CLEAR_STATUS, see Table 15.
                    wValue          |Reserved. Must be 0x0000.
                    wIndex          |Must specify interface number per the USB 2.0 specification, section 9.3.4.
                    wLength         |0x0002. Number of bytes to transfer per the USB 2.0 specification, section 9.3.5.
                    """
                    """ Table 34 -- CHECK_CLEAR_STATUS response format
                    Offset  |Field          |Size   |Value  |Description
                    ------------------------------------------------------------------------------------------------------------------------
                    0       |USBTMC_status  |1      |Value  |Status indication for this request. See Table 35.
                    1       |bmClear        |1      |Bitmap |D7...D1    |Reserved. All bits must be 0.
                            |               |       |       |D0         |BulkInFifoBytes
                            |               |       |       |           |1 - The device either has some queued DATA bytes
                            |               |       |       |           |in the Bulk-IN FIFO that it could not remove,
                            |               |       |       |           |or has a short packet that needs to be sent to
                            |               |       |       |           |the Host. The USBTMC_status must not be
                            |               |       |       |           |STATUS_SUCCESS.
                            |               |       |       |           |0 – The device has completely removed queued
                            |               |       |       |           |DATA in the Bulk-IN FIFO and the Bulk-IN
                            |               |       |       |           |FIFO is empty.
                    """
                    resp = Descriptor(bytearray(2))
                    resp.pack("BB", _TMC_STATUS_SUCCESS, 0)
                    return resp.b
                elif bRequest == _REQ_GET_CAPABILITIES:
                    # _REQ_GET_CAPABILITIES = const(7)  # 0xA1 (Dir = IN, Type = Class, Recipient = Interface)
                    return self.get_capabilities()
                elif bRequest == _REQ_INDICATOR_PULSE:
                    """ Table 38 -- INDICATOR_PULSE Setup packet
                    bmRequestType   |0xA1 (Dir = IN, Type = Class, Recipient = Interface)
                    bRequest        |INDICATOR_PULSE, see Table 15.
                    wValue          |0x0000
                    wIndex          |Must specify interface number per the USB 2.0 specification, section 9.3.4.
                    wLength         |0x0001. Number of bytes to transfer per the USB 2.0 specification, section 9.3.5.
                    """
                    """ Table 39 -- INDICATOR_PULSE response format
                    Offset  |Field          |Size   |Value  |Description
                    ------------------------------------------------------------------------------------------------------------------------
                    0       |USBTMC_status  |1      |Value  |Status indication for this request. See Table 32.
                    """
                    if self.indicator_pulse:
                        return resp.b
                    else:
                        return False
                else:
                    return False  # Unsupported request
            else:
                return False  # Unsupported request
        return True  # Unsupported request

    def on_endpoint_control_xfer(self, stage, request):
        # Control transfer callback. Override to handle a device
        # control transfer where bmRequestType Recipient is Endpoint and
        # the lower byte of wIndex indicates an endpoint address associated
        # with this interface.
        #
        # bmRequestType Type will generally have any value except
        # utils.REQ_TYPE_STANDARD, as Standard endpoint requests are handled by
        # TinyUSB. The exception is the the Standard "Set Feature" request. This
        # is handled by Tiny USB but also passed through to the driver in case it
        # needs to change any internal state, but most drivers can ignore and
        # return False in this case.
        #
        # (See USB 2.0 specification 9.4 Standard Device Requests, p250).
        #
        # See on_device_control_xfer() for a description of the parameters and
        # possible return values.
        bmRequestType, bRequest, wValue, wIndex, wLength = struct.unpack("BBHHH", request)

        recipient, req_type, data_direction = split_bmRequestType(bmRequestType)
        resp = Descriptor(bytearray(1))
        resp.pack("B", _TMC_STATUS_SUCCESS)

        if stage == _STAGE_SETUP:
            if req_type == _REQ_TYPE_STANDARD:
                return False  # Let tinyUSB work
            elif req_type == _REQ_TYPE_CLASS:
                if bRequest == _REQ_INITIATE_ABORT_BULK_OUT:
                    """ Table 18 -- INITIATE_ABORT_BULK_OUT Setup packet
                    bmRequestType   |0xA2 (Dir = IN, Type = Class, Recipient = Endpoint)
                    bRequest        |INITIATE_ABORT_BULK_OUT (1), see Table 15.
                    wValue          |D7...D0    |The bTag value associated with the transfer to abort.
                                    |D15...D8   |Reserved. Must be 0x00.
                    """
                    """ Table 19 -- INITIATE_ABORT_BULK_OUT response packet
                    Offset  |Field          |Size   |Value  |Description
                    ------------------------------------------------------------------------------------------------------------------------
                    0       |USBTMC_status  |1      |Value  |Status indication for this request. See Table 20.
                    1       |bTag           |1      |Value  |The bTag for the the current Bulk-OUT transfer. If there is no current
                            |               |       |       |Bulk-OUT transfer, bTag must be set to the bTag for the most recent
                            |               |       |       |bulk-OUT transfer. If no Bulk-OUT transfer has ever been started, bTag
                            |               |       |       |must be 0x00.
                    """
                    resp = Descriptor(bytearray(2))
                    resp.pack("BB", _TMC_STATUS_SUCCESS, wValue & 0xff)
                    return resp.b
                elif bRequest == _REQ_CHECK_ABORT_BULK_OUT_STATUS:
                    """Table 18 -- INITIATE_ABORT_BULK_OUT Setup packet
                    bmRequestType   |0xA2 (Dir = IN, Type = Class, Recipient = Endpoint)
                    bRequest        |INITIATE_ABORT_BULK_OUT, see Table 15.
                    wValue          |D7...D0    |The bTag value associated with the transfer to abort.
                                    |D15...D8   |Reserved. Must be 0x00.
                    wIndex          |Must specify direction and endpoint number per the USB 2.0 specification, section 9.3.4.
                    wLength         |0x0002. Number of bytes to transfer per the USB 2.0 specification, section 9.3.5.
                    """
                    """ Table 19 -- INITIATE_ABORT_BULK_OUT response packet
                    Offset  |Field          |Size   |Value  |Description
                    ------------------------------------------------------------------------------------------------------------------------
                    0       |USBTMC_status  |1      |Value  |Status indication for this request. See Table 20.
                    1       |bTag           |1      |Value  |The bTag for the the current Bulk-OUT transfer. If there is no current
                            |               |       |       |Bulk-OUT transfer, bTag must be set to the bTag for the most recent
                            |               |       |       |bulk-OUT transfer. If no Bulk-OUT transfer has ever been started, bTag
                            |               |       |       |must be 0x00.
                    """
                    resp = Descriptor(bytearray(2))
                    resp.pack("BB", _TMC_STATUS_SUCCESS, wValue & 0xff)
                    return resp.b
                elif bRequest == _REQ_INITIATE_ABORT_BULK_IN:
                    """ Table 21 -- CHECK_ABORT_BULK_OUT_STATUS Setup packet
                    bmRequestType   |0xA2 (Dir = IN, Type = Class, Recipient = Endpoint)
                    bRequest        |CHECK_ABORT_BULK_OUT_STATUS, see Table 15.
                    wValue          |Reserved. Must be 0x0000.
                    wIndex          |Must specify direction and endpoint number per the USB 2.0 specification, section 9.3.4.
                    wLength         |0x0008. Number of bytes to transfer per the USB 2.0 specification, section 9.3.5.
                    """
                    """ Table 22 -- CHECK_ABORT_BULK_OUT_STATUS response format
                    Offset  |Field          |Size   |Value      |Description
                    ------------------------------------------------------------------------------------------------------------------------
                    0       |USBTMC_status  |1      |Value      |Status indication for this request. See Table 23.
                    1-3     |Reserved       |3      |0x000000   |Reserved. Must be 0x000000.
                    4       |NBYTES_RXD     |4      |Number     |The total number of USBTMC message data bytes (not including
                            |               |       |           |Bulk-OUT Header or alignment bytes) in the transfer received,
                            |               |       |           |and not discarded, by the device. The device must always send
                            |               |       |           |NBYTES_RXD bytes to the Function Layer. Sent least significant
                            |               |       |           |byte first, most significant byte last.
                    """
                    resp = Descriptor(bytearray(8))
                    resp.pack("<B3xI", _TMC_STATUS_SUCCESS, 0x00)
                    return resp.b
                elif bRequest == _REQ_CHECK_ABORT_BULK_IN_STATUS:
                    """ Table 24 -- INITIATE_ABORT_BULK_IN Setup packet
                    bmRequestType   |0xA2 (Dir = IN, Type = Class, Recipient = Endpoint)
                    bRequest        |INITIATE_ABORT_BULK_IN, see Table 15.
                    wValue          |D7...D0    |The bTag value associated with the transfer to abort.
                                    |D15...D8   |Reserved. Must be 0x00.
                    wIndex          |Must specify direction and endpoint number per the USB 2.0 specification, section 9.3.4.
                    wLength         |0x0002. Number of bytes to transfer per the USB 2.0 specification, section 9.3.5.
                    """
                    """ Table 25 -- INITIATE_ABORT_BULK_IN response format
                    Offset  |Field          |Size   |Value  |Description
                    ------------------------------------------------------------------------------------------------------------------------
                    0       |USBTMC_status  |1      |Value  |Status indication for this request. See Table 26.
                    1       |bTag           |1      |Value  |The bTag for the current Bulk-IN transfer. If there is no current
                            |               |       |       |Bulk-IN transfer, bTag must be set to the bTag for the most recent
                            |               |       |       |bulk-IN transfer. If no Bulk-IN transfer has ever been started, bTag
                            |               |       |       |must be 0x00.
                    """
                    resp = Descriptor(bytearray(2))
                    resp.pack("BB", _TMC_STATUS_SUCCESS, wValue & 0xff)
                    return resp.b
                else:
                    return False  # Unsupported request
            else:
                return False  # Unsupported request
        return False  # Unsupported request

    def get_capabilities(self):
        interface_capability = ((1 if self.indicator_pulse else 0) << 2) | ((1 if self.talk_only else 0) << 1) | \
                               ((1 if self.listen_only else 0) << 0)

        resp = Descriptor(bytearray(6 + 6 + 12))
        resp.pack_into("BBHBB",
                       0,
                       _TMC_STATUS_SUCCESS,
                       0,
                       _bcdUSBTMC,
                       interface_capability,
                       1 if self.termchar else 0,
                       )
        return resp.b

    def _tx_xfer(self):
        # Keep an active IN transfer to send data to the host, whenever
        # there is data to send.
        if self.is_open() and not self.xfer_pending(self.ep_in) and self._tx.readable():
            self.submit_xfer(self.ep_in, self._tx.pend_read(), self._tx_cb)

    def _tx_cb(self, ep, res, num_bytes):
        if res == 0:
            self._tx.finish_read(num_bytes)
        self._tx_xfer()

    def _rx_xfer(self):
        # Keep an active OUT transfer to receive MIDI events from the host
        if self.is_open() and not self.xfer_pending(self.ep_out) and self._rx.writable():
            self.submit_xfer(self.ep_out, self._rx.pend_write(), self._rx_cb)

    def _rx_cb(self, ep, res, num_bytes):
        if res == 0:
            self._rx.finish_write(num_bytes)
            schedule(self._on_rx, None)
        self._rx_xfer()

    def on_open(self):
        super().on_open()
        # kick off any transfers that may have queued while the device was not open
        self._tx_xfer()
        self._rx_xfer()

    def _on_rx(self, _):
        """ Receive USBTMC messages. Called via micropython.schedule, outside of the USB callback function.

        :param _: dummy argument for micropython.schedule()
        """
        message: memoryview = self._rx.pend_read()
        self.on_bulk_out(message)
        self._rx.finish_read(len(message))

    def on_bulk_out(self, new_message: memoryview):
        """ Selects callbacks by given megID
        :param new_message:
        :return:
        """
        if not self._bulkout_header_processed:
            print("process header\n")
            msg_id, b_tag, b_tag_inverse, tmc_specific = struct.unpack_from("BBBx8s", new_message, 0)
            if (b_tag ^ b_tag_inverse) == 0xff:
                if msg_id in (_MSGID_DEV_DEP_MSG_OUT, _MSGID_VENDOR_SPECIFIC_OUT,
                              _MSGID_REQUEST_DEV_DEP_MSG_IN, _MSGID_REQUEST_VENDOR_SPECIFIC_IN):
                    self.last_bulkout_msg = TmcBulkInOutMessage(msg_id=msg_id, b_tag=b_tag, tmc_specific=tmc_specific,
                                                                message=bytes(new_message[_BULK_OUT_HEADER_SIZE:]),
                                                                response=b"")
                    self._bulkout_header_processed = True
                    self.on_bulk_out(new_message)
                else:
                    print("Unknown message ID:", msg_id)
                print(self.last_bulkout_msg)
        else:
            print("process rest of message\n")
            msg_id, b_tag, tmc_specific, last_bulkout_msg, _ = self.last_bulkout_msg
            transfer_size, _ = struct.unpack_from("<IB3x", tmc_specific, 0)
            print("on_bulk_out Transfer size:", transfer_size)

            if msg_id in (_MSGID_DEV_DEP_MSG_OUT, _MSGID_VENDOR_SPECIFIC_OUT):
                # last_bulkout_msg: bytes = self.last_bulkout_msg.message
                if transfer_size > len(last_bulkout_msg):  # need to receive more
                    message = last_bulkout_msg + bytes(new_message)  # concat message
                    self.last_bulkout_msg = TmcBulkInOutMessage(msg_id=msg_id, b_tag=b_tag, tmc_specific=tmc_specific,
                                                                message=message,
                                                                response=b"")
                    self._rx_xfer()  # receive more
                else:
                    if msg_id == _MSGID_DEV_DEP_MSG_OUT:
                        self.on_device_dependent_out()
                        self._bulkout_header_processed = False
                    elif msg_id == _MSGID_VENDOR_SPECIFIC_OUT:  # Unlikely the case
                        self.on_vendor_specific_out()
                        self._bulkout_header_processed = False
            elif msg_id == _MSGID_REQUEST_DEV_DEP_MSG_IN:
                self.on_request_device_dependent_in()
                self._bulkout_header_processed = False
            elif msg_id == _MSGID_REQUEST_VENDOR_SPECIFIC_IN:  # Unlikely the case
                self.on_request_vendor_specific_in()
                self._bulkout_header_processed = False
        print("self._bulkout_header_processed:", self._bulkout_header_processed)

    def on_device_dependent_out(self) -> None:
        """ Action on Bulk out transfer with megID==DEV_DEP_MSG_OUT.
        Subclasses must override this method.
        """
        """ Table 3 -- DEV_DEP_MSG_OUT Bulk-OUT Header with command specific content
                    |Offset  |Field          |Size   |Value          |Description
        ------------------------------------------------------------------------------------------------------------------------
                    |0-3     |See Table 1.   |4      |See Table 1.   |See Table 1.
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |4-7     |TransferSize   |4      |Number         |Total number of USBTMC message data bytes to be
        command     |        |               |       |               |sent in this USB transfer. This does not include the
        specific    |        |               |       |               |number of bytes in this Bulk-OUT Header or
        content     |        |               |       |               |alignment bytes. Sent least significant byte first,
                    |        |               |       |               |most significant byte last. TransferSize must be >
                    |        |               |       |               |0x00000000.
                    |8       |bmTransfer     |1      |Bitmap         |D7...D1   |Reserved. All bits must be 0.
                    |        |Attributes     |       |               |D0        |EOM.
                    |        |               |       |               |          |1 - The last USBTMC message data byte
                    |        |               |       |               |          |   in the transfer is the last byte of the
                    |        |               |       |               |          |   USBTMC message.
                    |        |               |       |               |          |0 – The last USBTMC message data byte
                    |        |               |       |               |          |   in the transfer is not the last byte of
                    |        |               |       |               |          |   the USBTMC message.
                    |9-11    |Reserved       |3      |0x000000       |Reserved. Must be 0x000000.
        """
        transfer_size, attribute = struct.unpack_from("<IB3x", self.last_bulkout_msg.tmc_specific, 0)
        print("Transfer size:", transfer_size)
        print("Attribute:", attribute)
        print("Message:", bytes(self.last_bulkout_msg.message))

    def draft_bulk_in_header(self, msg_id: int, b_tag: int, transfer_size: int) -> Descriptor:
        """ Draft a bulk in header. Subclasses may override this method.

        :param msg_id:
        :param b_tag:
        :param transfer_size:
        :return Descriptor:
        """
        """ Table 8 -- USBTMC Bulk-IN Header
        Offset  |Field                              |Size   |Value      |Description
        ------------------------------------------------------------------------------------------------------------------------
        0       |MsgID                              |1      |Value      |Must match MsgID in the USBTMC command
                |                                   |       |           |message transfer causing this response.
        1       |bTag                               |1      |Value      |Must match bTag in the USBTMC command message
                |                                   |       |           |transfer causing this response.
        2       |bTagInverse                        |1      |Value      |Must match bTagInverse in the USBTMC command
                |                                   |       |           |message transfer causing this response.
        3       |Reserved                           |1      |0x00       |Reserved. Must be 0x00.
        4-11    |USBTMC response message specific   |8      |USBTMC     | USBTMC response message specific. See section 3.3.1.
                |                                   |       |response   |
                |                                   |       |message    |
                |                                   |       |specific   |
        """
        assert msg_id in (_MSGID_DEV_DEP_MSG_IN, _MSGID_VENDOR_SPECIFIC_IN)
        resp = Descriptor(bytearray(transfer_size))
        resp.pack_into("BBB",
                       0,
                       msg_id,
                       b_tag & 0xff,
                       (~b_tag) & 0xff
                       )
        return resp

    def on_request_device_dependent_in(self) -> None:
        """ Action on Bulk out transfer with megID==REQUEST_DEV_DEP_MSG_IN.
        Subclasses must override this method.
        """
        """ Table 4 -- REQUEST_DEV_DEP_MSG_IN Bulk-OUT Header with command specific content
                    |Offset |Field          |Size   |Value          |Description
        ------------------------------------------------------------------------------------------------------------------------
                    |0-3    |See Table 1.   |4      |See Table 1.   |See Table 1.
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |4-7    |TransferSize   |4      |Number         |Total number of USBTMC message data bytes to be
        command     |       |               |       |               |sent in this USB transfer. This does not include the
        specific    |       |               |       |               |number of bytes in this Bulk-OUT Header or
        content     |       |               |       |               |alignment bytes. Sent least significant byte first,
                    |       |               |       |               |most significant byte last. TransferSize must be >
                    |       |               |       |               |0x00000000.
                    |8      |bmTransfer     |1      |Bitmap         |D7...D2    |Reserved. All bits must be 0.
                    |       |Attributes     |       |               |D1         |TermCharEnabled.
                    |       |               |       |               |           |1 – The Bulk-IN transfer must terminate
                    |       |               |       |               |           |   on the specified TermChar. The Host
                    |       |               |       |               |           |   may only set this bit if the USBTMC
                    |       |               |       |               |           |   interface indicates it supports
                    |       |               |       |               |           |   TermChar in the GET_CAPABILITIES
                    |       |               |       |               |           |   response packet.
                    |       |               |       |               |           |0 – The device must ignore TermChar.
                    |       |               |       |               |D0         |Must be 0.
                    |9      |TermChar       |1      |Value          |If bmTransferAttributes.D1 = 1, TermChar is an 8-bit
                    |       |               |       |               |value representing a termination character. If
                    |       |               |       |               |supported, the device must terminate the Bulk-IN
                    |       |               |       |               |transfer after this character is sent.
                    |       |               |       |               |If bmTransferAttributes.D1 = 0, the device must ignore
                    |       |               |       |               |this field.
                    |10-11  |Reserved       |2      |0x0000         |Reserved. Must be 0x0000.
        """
        transfer_size, attribute, termchar = struct.unpack_from("<IBB2x", self.last_bulkout_msg.tmc_specific, 0)

        header: Descriptor = self.draft_device_dependent_in_header(self.last_bulkout_msg.b_tag, transfer_size)
        message: bytes = self.prepare_dev_dep_msg_in()

        self.send_device_dependent_in(header, message)

    def prepare_dev_dep_msg_in(self) -> bytes:
        """ Prepares Bulk-IN transfer message.
        Subclasses must override this method.
        """
        ret = f"REQUEST_DEV_DEP_MSG_IN; last msgID = 0x{self.last_bulkout_msg.msg_id:02x}\n"
        return ret.encode()

    def draft_device_dependent_in_header(self, b_tag: int, transfer_size: int = 256):
        """ Draft a bulk in header for DEV_DEP_MSG_IN message

        :param b_tag:
        :param transfer_size:
        :return Descriptor:
        """
        """ Table 9 -- DEV_DEP_MSG_IN Bulk-IN Header with response specific content
                    |Offset |Field                              |Size   |Value          |Description
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |0-3    |See Table 8.                       |4      |See Table 8.   |See Table 8.
        response    |4-7    |TransferSize                       |4      |Number         |Total number of message data bytes to be sent in this
        specific    |       |                                   |       |               |USB transfer. This does not include the number of bytes
        content     |       |                                   |       |               |in this header or alignment bytes. Sent least significant
                    |       |                                   |       |               |byte first, most significant byte last. TransferSize must be
                    |       |                                   |       |               |> 0x00000000.
                    |8      |bmTransferAttributes               |1      |Bitmap         |D7...D2    |Reserved. All bits must be 0.
                    |       |                                   |       |               |D1         |1 – All of the following are true:
                    |       |                                   |       |               |           |   - The USBTMC interface supports
                    |       |                                   |       |               |           |       TermChar
                    |       |                                   |       |               |           |   - The bmTransferAttributes.
                    |       |                                   |       |               |           |       TermCharEnabled bit was set in the
                    |       |                                   |       |               |           |       REQUEST_DEV_DEP_MSG_IN.
                    |       |                                   |       |               |           |   - The last USBTMC message data byte in
                    |       |                                   |       |               |           |       this transfer matches the TermChar in
                    |       |                                   |       |               |           |       the REQUEST_DEV_DEP_MSG_IN.
                    |       |                                   |       |               |           |0 – One or more of the above conditions is
                    |       |                                   |       |               |           |   not met.
                    |       |                                   |       |               |D0         |EOM.
                    |       |                                   |       |               |           |1 - The last USBTMC message data byte in
                    |       |                                   |       |               |           |   the transfer is the last byte of the
                    |       |                                   |       |               |           |   USBTMC message.
                    |       |                                   |       |               |           |0 – The last USBTMC message data byte in
                    |       |                                   |       |               |           |   the transfer is not the last byte of the
                    |       |                                   |       |               |           |   USBTMC message.
                    |9-11   |Reserved                           |3      |0x000000       |Reserved. Must be 0x000000.
        """
        attr = (1 if self.termchar else 0) << 1 | 1
        header: Descriptor = self.draft_bulk_in_header(_MSGID_DEV_DEP_MSG_IN, b_tag, transfer_size)
        header.pack_into("B", 8, attr)

        return header

    def on_vendor_specific_out(self) -> None:
        """ Action on Bulk out transfer with megID==VENDOR_SPECIFIC_OUT
        Subclasses must override this method.
        """
        """ Table 5 -- VENDOR_SPECIFIC_OUT Bulk-OUT Header with command specific content
                    |Offset |Field          |Size   |Value          |Description
        ------------------------------------------------------------------------------------------------------------------------
                    |0-3    |See Table 1.   |4      |See Table 1.   |See Table 1.
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |4-7    |TransferSize   |4      |Number         |Total number of USBTMC message data bytes to be
        command     |       |               |       |               |sent in this USB transfer. This does not include the
        specific    |       |               |       |               |number of bytes in this Bulk-OUT Header or
        content     |       |               |       |               |alignment bytes. Sent least significant byte first,
                    |       |               |       |               |most significant byte last. TransferSize must be >
                    |       |               |       |               |0x00000000.
                    |8-11   |Reserved       |4      |0x00000000     |Reserved. Must be 0x0000000.
        """
        transfer_size = struct.unpack_from("<I4x", self.last_bulkout_msg.tmc_specific, 0)
        print("Transfer size:", transfer_size)

    def on_request_vendor_specific_in(self) -> None:
        """ Action on Bulk out transfer with megID==REQUEST_VENDOR_SPECIFIC_IN
        Subclasses must override this method.
        """
        """ Table 6 -- REQUEST_VENDOR_SPECIFIC_IN Bulk-OUT Header with command specific content
                    |Offset |Field          |Size   |Value          |Description
        ------------------------------------------------------------------------------------------------------------------------
                    |0-3    |See Table 1.   |4      |See Table 1.   |See Table 1.
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |4-7    |TransferSize   |4      |Number         |Total number of USBTMC message data bytes to be
        command     |       |               |       |               |sent in this USB transfer. This does not include the
        specific    |       |               |       |               |number of bytes in this Bulk-OUT Header or
        content     |       |               |       |               |alignment bytes. Sent least significant byte first,
                    |       |               |       |               |most significant byte last. TransferSize must be >
                    |       |               |       |               |0x00000000.
                    |8-11   |Reserved       |4      |0x00000000     |Reserved. Must be 0x00000000.
        """
        transfer_size = struct.unpack_from("<I4x", self.last_bulkout_msg.tmc_specific, 0)
        header: Descriptor = self.draft_vendor_specific_in_header(self.last_bulkout_msg.b_tag, transfer_size)
        print("Transfer size:", transfer_size)

    def draft_vendor_specific_in_header(self, b_tag, transfer_size):
        """ Draft a bulk in header for DEV_DEP_MSG_IN message
        :param b_tag:
        :param transfer_size:
        :return Descriptor:
        """
        """ Table 10 – VENDOR_SPECIFIC_IN Bulk-IN Header with response specific content
                    |Offset |Field                              |Size   |Value          |Description
        ------------------------------------------------------------------------------------------------------------------------
        USBTMC      |0-3    |See Table 8.                       |4      |See Table 8.   |See Table 8.
        response    |4-7    |TransferSize                       |4      |Number         |Total number of message data bytes to be sent in this
        specific    |       |                                   |       |               |USB transfer. This does not include the number of bytes
        content     |       |                                   |       |               |in this header or alignment bytes. Sent least significant
                    |       |                                   |       |               |byte first, most significant byte last. TransferSize must be
                    |       |                                   |       |               |> 0x00000000.
                    |8-11   |Reserved                           |4      |0x00000000     |Reserved. Must be 0x00000000.
        """
        header: Descriptor = self.draft_bulk_in_header(_MSGID_VENDOR_SPECIFIC_IN, b_tag, transfer_size)

        return header

    def send_device_dependent_in(self, header: Descriptor, message=b""):
        """
        :param header:
        :param message:
        :return bool:
        """
        if self.last_bulkout_msg.msg_id == _MSGID_REQUEST_DEV_DEP_MSG_IN:
            mes_len = len(message)
            header.pack_into("<I", 4, mes_len)
            padding_len = _HEADERS_BASE_SIZE - (len(message) % _HEADERS_BASE_SIZE)
            end_pos = _BULK_IN_HEADER_SIZE + mes_len + padding_len

            assert end_pos % _HEADERS_BASE_SIZE == 0
            print(end_pos, end_pos % 16)

            header.pack_into(f"{mes_len}B", 12, *list(message))
            p = 0
            while p < end_pos:
                e = min(end_pos - p, _wMaxPacketSize)
                e = self._tx.write(header.b[p:p + e])  # get actual written bytes
                print(e)
                self._tx_xfer()
                p += e
            return True

        return False
