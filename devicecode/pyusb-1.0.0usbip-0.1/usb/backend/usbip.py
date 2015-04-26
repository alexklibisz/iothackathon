# pyusb usbip backend
# connects to usbip server
# 3/18/2014 Rob Liston
#
# vim: set ts=4 sw=4 expandtab

import os
import socket
import struct
import array
import usb.backend
import usb._interop as _interop

__author__ = 'Rob Liston'
__all__ = ['get_backend']

class usb_descriptor: pass

class backend(usb.backend.IBackend):
    def __init__(self, server, debug):
        self.devices = {}
        self.server = server
        self.debug = debug

    def recvall(self, sock, n):
        # recv n bytes or return None if EOF is hit
        data = ''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def enumerate_devices(self):
        if self.debug:
            print "enumerate_devices()"

        for i in range(0, 3):
            # fetch the list of active device identifiers 'busnum-devnum'
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server, 3240))
            # send OP_REQ_DEVLIST
            s.send(struct.pack('!HHL', 0, 0x8005, 0))
            # first 12 bytes of response are fixed length
            response = struct.unpack('!HHLL', s.recv(12))
            ndevs = response[3]
            busid = []

            while ndevs:
                # device = struct.unpack('=256s32sLLLHHHBBBBBB', s.recv(312))                         # each device descriptor is 312 bytes
                device = struct.unpack('=256s32sLLLHHHBBBBBB', self.recvall(s, 312))                         # each device descriptor is 312 bytes
                busid.append(device[1].split('\x00', 1)[0])                                         # save busid string e.g '1-1'
                bNumInterfaces = device[13]
                while bNumInterfaces:
                    interface = struct.unpack('=BBBB', s.recv(4))                                   # each interface descriptor is 4 bytes
                    bNumInterfaces -= 1
                ndevs -= 1
            s.close()

        # if !(new in old) then fetch descriptors
        for new in busid:
            if new not in self.devices.keys():
                dev = self.fetch_descriptors(new)
                if (dev != None):
                    if self.debug:
                        print "adding new device=", new
                    self.devices[new] = dev

        # if !(old in new) then delete old
        for old in self.devices.keys():
            if old not in busid:
                if self.debug:
                    print "deleting old device=", old
                del self.devices[old]

        return self.devices


    def fetch_descriptors(self, busid):
        if self.debug:
            print "fetch_descriptors(", busid, ")"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server, 3240))
        s.send(struct.pack('!HHL32s', 0, 0x8003, 0, busid))                                     # send OP_REQ_IMPORT
        response = struct.unpack('!HHL', s.recv(8))                                             # first 8 bytes of response are fixed length
        if response[2]:
            # print "received error response to REQ_IMPORT, closing socket"
            s.close()
            return None
        response = struct.unpack('!256s32sLLLHHHBBBBBB', s.recv(312))
        bus = response[2];
        address = int(response[0][0:12], 16)

        descriptors = {}

        # fetch device_descriptor
        s.send(struct.pack('!10L', 1, 0, 0, 1, 0, 0, 18, 0, 0, 0))                              # send USBIP_CMD_SUBMIT
        s.send(struct.pack('<BBHHH', 0x80, 0x06, 0x0100, 0, 18))                                # send USB setup packet
        response = struct.unpack('!10L8B', s.recv(48))
        actual_length = response[6]
        response = struct.unpack('<BBHBBBBHHHBBBB', s.recv(actual_length))
        usb_device_descriptor = usb_descriptor()
        setattr(usb_device_descriptor, 'bLength', response[0])
        setattr(usb_device_descriptor, 'bDescriptorType', response[1])
        setattr(usb_device_descriptor, 'bcdUSB', response[2])
        setattr(usb_device_descriptor, 'bDeviceClass', response[3])
        setattr(usb_device_descriptor, 'bDeviceSubClass', response[4])
        setattr(usb_device_descriptor, 'bDeviceProtocol', response[5])
        setattr(usb_device_descriptor, 'bMaxPacketSize0', response[6])
        setattr(usb_device_descriptor, 'idVendor', response[7])
        setattr(usb_device_descriptor, 'idProduct', response[8])
        setattr(usb_device_descriptor, 'bcdDevice', response[9])
        setattr(usb_device_descriptor, 'iManufacturer', response[10])
        setattr(usb_device_descriptor, 'iProduct', response[11])
        setattr(usb_device_descriptor, 'iSerialNumber', response[12])
        setattr(usb_device_descriptor, 'bNumConfigurations', response[13])
        setattr(usb_device_descriptor, 'address', address)
        setattr(usb_device_descriptor, 'bus', bus)
        setattr(usb_device_descriptor, 'port_number', None)
        descriptors['device'] = usb_device_descriptor

        for ncfg in range(0, getattr(usb_device_descriptor, 'bNumConfigurations')):
            # fetch configuration_descriptor
            s.send(struct.pack('!10L', 1, 0, 0, 1, 0, 0, 9, 0, 0, 0))                          # send USBIP_CMD_SUBMIT
            s.send(struct.pack('<BBHHH', 0x80, 0x06, 0x0200, 0, 9))                            # send USB setup packet
            response = struct.unpack('!10L8B', s.recv(48))
            actual_length = response[6]
            response = struct.unpack('<BBHBBBBB', s.recv(actual_length))
            wTotalLength = response[2]
            s.send(struct.pack('!10L', 1, 0, 0, 1, 0, 0, wTotalLength, 0, 0, 0))              # send USBIP_CMD_SUBMIT
            s.send(struct.pack('<BBHHH', 0x80, 0x06, 0x0200, 0, wTotalLength))                # send USB setup packet
            response = struct.unpack('!10L8B', s.recv(48))
            actual_length = response[6]
            response = struct.unpack('<BBHBBBBB', s.recv(9))
            usb_configuration_descriptor = usb_descriptor()
            setattr(usb_configuration_descriptor, 'bLength', response[0])
            setattr(usb_configuration_descriptor, 'bDescriptorType', response[1])
            setattr(usb_configuration_descriptor, 'wTotalLength', response[2])
            setattr(usb_configuration_descriptor, 'bNumInterfaces', response[3])
            setattr(usb_configuration_descriptor, 'bConfigurationValue', response[4])
            setattr(usb_configuration_descriptor, 'iConfiguration', response[5])
            setattr(usb_configuration_descriptor, 'bmAttributes', response[6])
            setattr(usb_configuration_descriptor, 'bMaxPower', response[7])
            descriptors['configuration-'+str(ncfg)] = usb_configuration_descriptor

            bytes_read = 9 # length of configuration descriptor
            nifc = -1
            nept = -1
            while (bytes_read < actual_length):
                (length, type) = struct.unpack('<BB', s.recv(2))
                if (type == 0x04): # interface descriptor
                    nifc = nifc + 1
                    response = struct.unpack('<BBBBBBB', s.recv(7))
                    usb_interface_descriptor = usb_descriptor()
                    setattr(usb_interface_descriptor, 'bLength', length)
                    setattr(usb_interface_descriptor, 'bDescriptorType', type)
                    setattr(usb_interface_descriptor, 'bInterfaceNumber', response[0])
                    setattr(usb_interface_descriptor, 'bAlternateSetting', response[1])
                    setattr(usb_interface_descriptor, 'bNumEndpoints', response[2])
                    setattr(usb_interface_descriptor, 'bInterfaceClass', response[3])
                    setattr(usb_interface_descriptor, 'bInterfaceSubClass', response[4])
                    setattr(usb_interface_descriptor, 'bInterfaceProtocol', response[5])
                    setattr(usb_interface_descriptor, 'iInterface', response[6])
                    bAlternateSetting = getattr(usb_interface_descriptor, 'bAlternateSetting')
                    descriptors['interface-'+str(ncfg)+'-'+str(nifc)+'-'+str(bAlternateSetting)] = usb_interface_descriptor
                elif (type == 0x05): # endpoint descriptor
                    nept = nept + 1
                    response = struct.unpack('<BBHB', s.recv(5))
                    usb_endpoint_descriptor = usb_descriptor()
                    setattr(usb_endpoint_descriptor, 'bLength', length)
                    setattr(usb_endpoint_descriptor, 'bDescriptorType', type)
                    setattr(usb_endpoint_descriptor, 'bEndpointAddress', response[0] & 0xf)
                    setattr(usb_endpoint_descriptor, 'bmAttributes', response[1])
                    setattr(usb_endpoint_descriptor, 'wMaxPacketSize', response[2])
                    setattr(usb_endpoint_descriptor, 'bInterval', response[3])
                    setattr(usb_endpoint_descriptor, 'bRefresh', None)
                    setattr(usb_endpoint_descriptor, 'bSynchAddress', None)
                    descriptors['endpoint-'+str(ncfg)+'-'+str(nifc)+'-'+str(bAlternateSetting)+'-'+str(nept)] = usb_endpoint_descriptor
                else:
                    s.recv(length-2)

                bytes_read = bytes_read + length
        s.close()
        return descriptors

    def get_device_descriptor(self, dev):
        return self.devices[dev]['device']

    def get_configuration_descriptor(self, dev, config):
        return self.devices[dev]['configuration-'+str(config)]

    def get_interface_descriptor(self, dev, intf, alt, config):
        key = 'interface-'+str(config)+'-'+str(intf)+'-'+str(alt)
        if key in self.devices[dev]:
            return self.devices[dev][key]
        else:
            raise IndexError('Invalid descriptor index ' + key)

    def get_endpoint_descriptor(self, dev, ep, intf, alt, config):
        return self.devices[dev]['endpoint-'+str(config)+'-'+str(intf)+'-'+str(alt)+'-'+str(ep)]

    def open_device(self, dev):
        if self.debug:
            print "open_device(", dev, ")"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server, 3240))
        s.send(struct.pack('!HHL32s', 0, 0x8003, 0, dev))                                     # send OP_REQ_IMPORT
        response = struct.unpack('!HHL', s.recv(8))                                             # first 8 bytes of response are fixed length
        if response[2]:
            s.close()
            return None
        response = struct.unpack('!256s32sLLLHHHBBBBBB', s.recv(312))
        return s

    def close_device(self, dev_handle):
        dev_handle.close()

    def set_configuration(self, dev_handle, config_value):
        dev_handle.send(struct.pack('!10L', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0))                              # send USBIP_CMD_SUBMIT
        dev_handle.send(struct.pack('<BBHHH', 0x00, 0x09, config_value, 0, 0))                                # send USB setup packet
        response = struct.unpack('!10L8B', dev_handle.recv(48))

    def get_configuration(self, dev_handle):
        dev_handle.send(struct.pack('!10L', 1, 0, 0, 1, 0, 0, 1, 0, 0, 0))                              # send USBIP_CMD_SUBMIT
        dev_handle.send(struct.pack('<BBHHH', 0x80, 0x08, 0, 0, 1))                                # send USB setup packet
        response = struct.unpack('!10L8B', dev_handle.recv(48))
        config_value = dev_handle.recv(1)
        return config_value

    def set_interface_altsetting(self, dev_handle, intf, altsetting):
        dev_handle.send(struct.pack('!10L', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0))                              # send USBIP_CMD_SUBMIT
        dev_handle.send(struct.pack('<BBHHH', 0x01, 0x11, altsetting, intf, 0))                                # send USB setup packet
        response = struct.unpack('!10L8B', dev_handle.recv(48))

    def bulk_write(self, dev_handle, ep, intf, data, timeout, submit, complete):
	if submit:
        	dev_handle.send(struct.pack('!10L8B', 1, 0, 0, 0, ep, 0, len(data), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))                              # send USBIP_CMD_SUBMIT
        	dev_handle.send(data);
	if complete:
        	response = struct.unpack('!10L8B', dev_handle.recv(48))
        	actual_length = response[6]
        	return actual_length

    def bulk_read(self, dev_handle, ep, intf, size, timeout, submit, complete):
	if submit:
        	dev_handle.send(struct.pack('!10L8B', 1, 0, 0, 1, ep, 0, size, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))                              # send USBIP_CMD_SUBMIT
	if complete:
        	response = struct.unpack('!10L8B', dev_handle.recv(48))
        	actual_length = response[6]
        	return array.array('B', dev_handle.recv(actual_length))

    def intr_write(self, dev_handle, ep, intf, data, timeout, submit, complete):
	if submit:
        	dev_handle.send(struct.pack('!10L8B', 1, 0, 0, 0, ep, 0, len(data), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))                              # send USBIP_CMD_SUBMIT
        	dev_handle.send(data);
	if complete:
        	response = struct.unpack('!10L8B', dev_handle.recv(48))
        	actual_length = response[6]
        	return actual_length

    def intr_read(self, dev_handle, ep, intf, size, timeout, submit, complete):
	if submit:
        	dev_handle.send(struct.pack('!10L8B', 1, 0, 0, 1, ep, 0, size, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))                              # send USBIP_CMD_SUBMIT
	if complete:
        	response = struct.unpack('!10L8B', dev_handle.recv(48))
        	actual_length = response[6]
        	return array.array('B', dev_handle.recv(actual_length))

    def ctrl_transfer(self,
                      dev_handle,
                      bmRequestType,
                      bRequest,
                      wValue,
                      wIndex,
                      data_or_wLength,
                      timeout):
        if (bmRequestType & 0x80):  # IN
            dev_handle.send(struct.pack('!10L', 1, 0, 0, 1, 0, 0, data_or_wLength, 0, 0, 0))                              # send USBIP_CMD_SUBMIT
            dev_handle.send(struct.pack('<BBHHH', bmRequestType, bRequest, wValue, wIndex, data_or_wLength))                                # send USB setup packet
            response = struct.unpack('!10L8B', dev_handle.recv(48))
            actual_length = response[6]
            return array.array('B', dev_handle.recv(actual_length))
        else:   # OUT
            dev_handle.send(struct.pack('!10L', 1, 0, 0, 0, 0, 0, len(data_or_wLength), 0, 0, 0))                              # send USBIP_CMD_SUBMIT
            dev_handle.send(struct.pack('<BBHHH', bmRequestType, bRequest, wValue, wIndex, len(data_or_wLength)))                                # send USB setup packet
            dev_handle.send(data_or_wLength)
            response = struct.unpack('!10L8B', dev_handle.recv(48))
            actual_length = response[6]
            return actual_length

    def claim_interface(self, dev_handle, intf):
        pass

    def release_interface(self, dev_handle, intf):
        pass

def get_backend():
    if 'USBIP_SERVER' in os.environ:
        if 'USBIP_DEBUG' in os.environ:
            debug = os.environ['USBIP_DEBUG']
        else:
            debug = False
        if debug:
            print "get_backend(", os.environ['USBIP_SERVER'], ")"
        return backend(os.environ['USBIP_SERVER'], debug)
    else:
        return None
