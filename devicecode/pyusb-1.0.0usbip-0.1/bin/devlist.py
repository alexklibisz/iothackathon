import os, sys, getopt
import usb

try:
    opts, args = getopt.getopt(sys.argv[1:],"s:",["server="])
    valid = False
    for opt, arg in opts:
        if opt in ("-s", "--server"):
            os.environ["USBIP_SERVER"] = arg
            valid = True
except:
    valid = False

if not valid:
    print 'usage: devlist.py -s <server>'
    sys.exit()

devices = usb.core.find(find_all=True)
for dev in devices:
    dev.set_configuration()
    print usb.util.get_string(dev, 256, 1)
    print usb.util.get_string(dev, 256, 2)
    print usb.util.get_string(dev, 256, 3)
