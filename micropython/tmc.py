# MicroPython USB tmc module
#
# Test and Measurement Class
#
# MIT license; Copyright (c) 2025 Kazuki Yamamoto

from micropython import const
import machine
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
|Offset |Field              |Size   |Value          |Description
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
"""
_INTERFACE_CLASS_TMC = const(0xFE)
_INTERFACE_SUBCLASS_TMC = const(0x03)

"""
Table 44 -- USBTMC bInterfaceProtocol values
|bInterfaceProtocol Value   |Description
|0                          |USBTMC interface. No subclass specification applies.
|1                          |USBTMC USB488 interface. See the USB488 subclass specification.
|2-127                      |Reserved
"""
_PROTOCOL_NONE = const(0x00)
_PROTOCOL_488 = const(0x01)

"""
4.2 USBTMC class specific requests
All USBTMC class specific requests must be sent with a Setup packet as shown below in Table 14.

Table 14 -- USBTMC class specific request format
|Offset |Field          |Size   |Value      |Description
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
|       |               |       |           |D4...D0
|       |               |       |           |           Recipient               0 - Device
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
|bRequest   |Name                           |Required/Optional  |Comment
|           |                               |                   |
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
"""
# USBTMC bRequest values
_REQ_CONTROL_INITIATE_ABORT_BULK_OUT = const(1)
_REQ_CONTROL_CHECK_ABORT_BULK_OUT_STATUS = const(2)
_REQ_CONTROL_INITIATE_ABORT_BULK_IN = const(3)
_REQ_CONTROL_CHECK_ABORT_BULK_IN_STATUS = const(4)
_REQ_CONTROL_INITIATE_CLEAR = const(5)
_REQ_CONTROL_CHECK_CLEAR_STATUS = const(6)
_REQ_CONTROL_GET_CAPABILITIES = const(7)
_REQ_CONTROL_INDICATOR_PULSE = const(64)


class TMCInterface(Interface):
    def __init__(self, **kwargs):
        super().__init__()
        self.ep_out = None  # Set during enumeration. RX direction (host to device)
        self.ep_in = None  # TX direction (device to host)
        self._rx = Buffer(64)
        self._tx = Buffer(64)

    def desc_cfg(self, desc, itf_num, ep_num, strs):
        # Function to build configuration descriptor contents for this interface
        # or group of interfaces. This is called on each interface from
        # USBDevice.init().
        #
        # This function should insert:
        #
        # - At least one standard Interface descriptor (can call
        # - desc.interface()).
        desc.interface(itf_num, 0, _INTERFACE_CLASS_TMC, _INTERFACE_SUBCLASS_TMC, _PROTOCOL_488)

        # Plus, optionally:
        #
        # - One or more endpoint descriptors (can call desc.endpoint()).
        # - An Interface Association Descriptor, prepended before.
        # - Other class-specific configuration descriptor data.
        #
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
        return 2  # 1x Bulk IN|OUT + 1x Interrupt IN
