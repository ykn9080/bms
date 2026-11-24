import socket
import sys

from bacpypes.core import run, stop, deferred
from bacpypes.pdu import Address
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU
from bacpypes.iocb import IOCB
from bacpypes.primitivedata import Real
from bacpypes.constructeddata import Any

TARGET_IP = "172.18.0.20"
OBJ_TYPE = sys.argv[1] if len(sys.argv) > 1 else "analogValue"
OBJ_INSTANCE = int(sys.argv[2]) if len(sys.argv) > 2 else 0
NEW_VALUE = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0


def get_local_ip(target):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((target, 47808))
    ip = s.getsockname()[0]
    s.close()
    return ip


my_ip = get_local_ip(TARGET_IP)
device = LocalDeviceObject(
    objectName="BMSWriter",
    objectIdentifier=598,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15,
)
app = BIPSimpleApplication(device, f"{my_ip}/16")


def on_done(iocb):
    if iocb.ioResponse and isinstance(iocb.ioResponse, SimpleAckPDU):
        print(f"OK: {OBJ_TYPE},{OBJ_INSTANCE} presentValue <- {NEW_VALUE}")
    elif iocb.ioError:
        print("ERROR:", iocb.ioError)
    else:
        print("UNEXPECTED RESPONSE:", iocb.ioResponse)
    stop()


def write_once():
    value = Any()
    value.cast_in(Real(NEW_VALUE))
    req = WritePropertyRequest(
        objectIdentifier=(OBJ_TYPE, OBJ_INSTANCE),
        propertyIdentifier="presentValue",
    )
    req.propertyValue = value
    req.pduDestination = Address(TARGET_IP)
    iocb = IOCB(req)
    iocb.add_callback(on_done)
    app.request_io(iocb)


deferred(write_once)
run()
