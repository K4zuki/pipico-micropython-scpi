include("$(MPY_DIR)/ports/rp2/boards/manifest.py")
require("usb-device")

module("MicroScpiDevice.py", base_path="../")
module("RaspberryScpiPico.py", base_path="../")
module("tmc.py")
module("usb488.py")
module("Usb488ScpiPico.py")
module("main.py")
