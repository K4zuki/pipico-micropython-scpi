include("$(MPY_DIR)/ports/rp2/boards/manifest.py")
require("usb-device")

module("RaspberryScpiPico.py", base_path="../")
module("tmc.py", base_path="../")
module("usb488.py", base_path="../")
module("MicroScpiDevice.py", base_path="../")
module("Usb488ScpiPico.py", base_path="../")
module("main.py")
