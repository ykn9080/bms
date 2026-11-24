import os
import signal
import socket
import time
import urllib.parse
import urllib.request

from bacpypes.core import run, stop, deferred
from bacpypes.pdu import Address
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import ReadPropertyRequest
from bacpypes.iocb import IOCB
from bacpypes.primitivedata import Real

INFLUX_URL = os.environ["INFLUX_URL"]
INFLUX_TOKEN = os.environ["INFLUX_TOKEN"]
INFLUX_ORG = os.environ["INFLUX_ORG"]
EPMS_IP = os.environ.get("EPMS_IP", "172.18.0.21")
SITE_ID = os.environ.get("SITE_ID", "SITE_GN_PRIME")
TIMEOUT_SEC = 10

POINTS = [
    # EPMS → epms
    {"ip": EPMS_IP, "obj": "analogInput", "inst": 0, "point_id": "PT_B01_HV_KW",
     "bucket": "node_red_bucket", "measurement": "epms",
     "tags": {"site_id": SITE_ID, "asset_id": "AS_B01_HV_PNL_01", "unit": "kW"}},
    {"ip": EPMS_IP, "obj": "analogInput", "inst": 1, "point_id": "PT_B01_TR01_KW",
     "bucket": "node_red_bucket", "measurement": "epms",
     "tags": {"site_id": SITE_ID, "asset_id": "AS_B01_TR_01", "unit": "kW"}},
    {"ip": EPMS_IP, "obj": "analogInput", "inst": 2, "point_id": "PT_B01_LV_KW",
     "bucket": "node_red_bucket", "measurement": "epms",
     "tags": {"site_id": SITE_ID, "asset_id": "AS_B01_LV_MAIN_01", "unit": "kW"}},
    {"ip": EPMS_IP, "obj": "analogInput", "inst": 3, "point_id": "PT_FL19_DB_KW",
     "bucket": "node_red_bucket", "measurement": "epms",
     "tags": {"site_id": SITE_ID, "asset_id": "AS_FL19_DB_01", "unit": "kW"}},
]


def get_local_ip(target):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((target, 47808))
    ip = s.getsockname()[0]
    s.close()
    return ip


def write_influx(bucket, measurement, tags, value):
    tag_str = ",".join(f"{k}={v}" for k, v in tags.items())
    line = f"{measurement},{tag_str} value={value} {time.time_ns()}"
    params = urllib.parse.urlencode(
        {"org": INFLUX_ORG, "bucket": bucket, "precision": "ns"}
    )
    req = urllib.request.Request(
        f"{INFLUX_URL}/api/v2/write?{params}",
        data=line.encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Token {INFLUX_TOKEN}",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        print(f"WRITE {r.status} {bucket} {line}", flush=True)


def on_timeout(signum, frame):
    print("TIMEOUT: 응답 없음", flush=True)
    os._exit(1)


def main():
    signal.signal(signal.SIGALRM, on_timeout)
    signal.alarm(TIMEOUT_SEC)

    my_ip = get_local_ip(EPMS_IP)
    device = LocalDeviceObject(
        objectName="EPMSCollector",
        objectIdentifier=599,
        maxApduLengthAccepted=1024,
        segmentationSupported="noSegmentation",
        vendorIdentifier=15,
    )
    app = BIPSimpleApplication(device, f"{my_ip}/16")
    pending = set(range(len(POINTS)))

    def make_callback(idx, p):
        def callback(iocb):
            if iocb.ioResponse:
                try:
                    value = float(iocb.ioResponse.propertyValue.cast_out(Real))
                    tags = {"point_id": p["point_id"], **p["tags"]}
                    write_influx(p["bucket"], p["measurement"], tags, value)
                except Exception as e:
                    print(f"INFLUX ERROR {p['point_id']}: {e}", flush=True)
            else:
                print(f"BACNET ERROR {p['point_id']}: {iocb.ioError}", flush=True)
            pending.discard(idx)
            if not pending:
                stop()
        return callback

    def send_all():
        for idx, p in enumerate(POINTS):
            req = ReadPropertyRequest(
                objectIdentifier=(p["obj"], p["inst"]),
                propertyIdentifier="presentValue",
            )
            req.pduDestination = Address(p["ip"])
            iocb = IOCB(req)
            iocb.add_callback(make_callback(idx, p))
            app.request_io(iocb)

    deferred(send_all)
    run()
    signal.alarm(0)


if __name__ == "__main__":
    main()
