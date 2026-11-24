import socket

from bacpypes.core import run, stop, deferred
from bacpypes.pdu import Address
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import ReadPropertyRequest
from bacpypes.iocb import IOCB
from bacpypes.primitivedata import Real

TARGET_IP = "172.18.0.3"     # BACnet 시뮬레이터 주소
OBJ_TYPE = "analogInput"
OBJ_INSTANCE = 0
PROP = "presentValue"


def get_local_ip(target):
    # 대상 주소로 나가는 인터페이스의 IP를 찾습니다
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((target, 47808))
    ip = s.getsockname()[0]
    s.close()
    return ip


my_ip = get_local_ip(TARGET_IP)

device = LocalDeviceObject(
    objectName="BACpypesTester",
    objectIdentifier=599,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15,
)
app = BIPSimpleApplication(device, f"{my_ip}/16")


def on_done(iocb):
    if iocb.ioResponse:
        value = iocb.ioResponse.propertyValue.cast_out(Real)
        print(f"{OBJ_TYPE},{OBJ_INSTANCE} {PROP} = {value}")
    elif iocb.ioError:
        print("ERROR:", iocb.ioError)
    stop()


def read_once():
    req = ReadPropertyRequest(
        objectIdentifier=(OBJ_TYPE, OBJ_INSTANCE),
        propertyIdentifier=PROP,
    )
    req.pduDestination = Address(TARGET_IP)
    iocb = IOCB(req)
    iocb.add_callback(on_done)
    app.request_io(iocb)


deferred(read_once)
run()
