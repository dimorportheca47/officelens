from __future__ import absolute_import
from __future__ import print_function

import argparse
import json
import logging
import signal
import sys
import time
from datetime import datetime

from awscrt import io, mqtt
from awsiot import iotshadow, mqtt_connection_builder

from grovepi import * 

from requests_aws4auth import AWS4Auth
from botocore.session import Session

# - Overview -
# This sample shows 1) how to connect AWS IoT Core. 2) How to use AWS IoT
# Device Shadow

AllowedActions = ['both', 'publish', 'subscribe']

BASE_TOPIC = "data/"
DEFAULT_WAIT_TIME = 0.1
SHADOW_WAIT_TIME_KEY = "wait_time"
KEEP_ALIVE = 300

mqtt_connection = None
shadow_client = None
wait_time = DEFAULT_WAIT_TIME
device_name = None

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logging.basicConfig()


def arg_check():
    """
    argument check
    """

    logging.debug("start: arg_check")
    parser = argparse.ArgumentParser()
    parser.add_argument("--device_name", required=True,
                        help="[Must], AWS IoT Core Thing Name")
    parser.add_argument('--verbosity', choices=[x.name for x in io.LogLevel],
                        default=io.LogLevel.NoLogs.name, help='Logging level')
                        
    parser.add_argument("-e", "--endpoint", action="store", required=True, dest="endpoint", help="Your AWS IoT custom endpoint")
    parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCA", help="Root CA file path")
    parser.add_argument("-c", "--cert", action="store", dest="cert", help="Certificate file path")
    parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
    parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
    parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                        help="Use MQTT over WebSocket")
    parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
                        help="Targeted client id")

    args = parser.parse_args()

    log_level = getattr(io.LogLevel, args.verbosity, "error")
    io.init_logging(log_level, 'stderr')
    loglevel_map = [
        logging.INFO, logging.INFO, logging.INFO,
        logging.INFO, logging.INFO, logging.DEBUG,
        logging.DEBUG]
    logger.setLevel(loglevel_map[log_level])
    logging.basicConfig()

    cert_list = find_certs_file()
    if args.rootCA is not None:
        cert_list[0] = args.rootCA
    if args.privateKeyPath is not None:
        cert_list[1] = args.privateKeyPath
    if args.cert is not None:
        cert_list[2] = args.cert

    logging.debug(cert_list)
    file_exist_check(cert_list)

    init_dict = {
        "device_name": args.device_name,
        "endpoint": args.endpoint,
        "certs": cert_list
    }
    return init_dict

def device_main():
    """
    main loop for dummy device
    """
    global device_name, mqtt_connection, shadow_client

    init_info = arg_check()
    device_name = init_info['device_name']
    iot_endpoint = init_info['endpoint']
    rootca_file = init_info['certs'][0]
    private_key_file = init_info['certs'][1]
    certificate_file = init_info['certs'][2]

    logger.info("device_name: %s", device_name)
    logger.info("endpoint: %s", iot_endpoint)
    logger.info("rootca cert: %s", rootca_file)
    logger.info("private key: %s", private_key_file)
    logger.info("certificate: %s", certificate_file)

    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
    
    #Topic Settings
    prefix = "data"
    buildings = "DEMO"
    floor = "10F"
    seats = "10.X4"
    # deviceId = str(uuid.uuid5(uuid.NAMESPACE_DNS, "capstone"))
    deviceId = device_name
    topic = [prefix,buildings, floor, seats, deviceId]
    topic = "/".join(topic)    
    logging.info("topic: %s", topic)

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=iot_endpoint,
        cert_filepath=certificate_file,
        pri_key_filepath=private_key_file,
        client_bootstrap=client_bootstrap,
        ca_filepath=rootca_file,
        client_id=device_name,
        clean_session=False,
        keep_alive_secs=KEEP_ALIVE)
    print(mqtt_connection)

    connected_future = mqtt_connection.connect()
    shadow_client = iotshadow.IotShadowClient(mqtt_connection)
    connected_future.result()

    # grove setting
    led = 4
    set_bus("RPI_1")
    pinMode(led,"OUTPUT")

    # time as leaving seats
    timer = 50

    alias = "None" 
    while True:
        message = {
            "SensorID":deviceId,
            "IsOccupied":False,
            "TimeStamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        range = ultrasonicRead(ultrasonic_ranger)
        if timer:
            # 距離センサーの値が規定値より大さい場合はリセットタイマーをデクリメント
            if range > 15:
                timer -= 1

        if range >= 15 and timer <=0:
            digitalWrite(led, 1)
            message["IsOccupied"] = False
        else:
            digitalWrite(led, 0)
            message["IsOccupied"] = True
        print("timer: ", timer)
        # Publish to IoT Core
        logger.debug("  payload: %s", message)
        print(message)

        mqtt_connection.publish(
            topic=topic,
            payload=json.dumps(message),
            qos=mqtt.QoS.AT_LEAST_ONCE)
        time.sleep(wait_time)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_handler)

    device_main()
