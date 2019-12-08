import sys
import time
import ast
import click
import paho.mqtt.client as mqtt
import pyrebase
import requests


@click.command()
@click.option('--api-url', required=True)
def main(api_url=None):
    config = {
        "apiKey": "AIzaSyD9kyPxezXpH7mhRwWULwhrehEI-LaZjzY",
        "databaseURL": "https://smart-amplifier-gsyadn.firebaseio.com/",
        "authDomain": "smart-amplifier-gsyadn.firebaseapp.com",
        "storageBucket": "smart-amplifier-gsyadn.appspot.com"
    }

    devices = {}

    client = mqtt.Client()
    firebase = pyrebase.initialize_app(config).database()

    def stream_handler(message):
        try:
            volume = message['data']['volume']
        except TypeError:
            volume = message['data']

        print('Volume change for ID',
              message['stream_id'], 'to', str(volume))
        client.publish('node/{}/led-strip/-/volume/set'.format(
            devices[message['stream_id']]), '"{}"'.format(volume))

    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        client.subscribe('gateway/usb-dongle/nodes')
        client.publish('gateway/usb-dongle/nodes/get')

    def handler_device_list(client, userdata, msg):
        for device in ast.literal_eval(str(msg.payload, 'utf-8')):
            if not firebase.child('amplifiers').child(device['id']).child('volume').get().val():
                requests.post('{}/register/new/amplifier'.format(api_url), {
                              "amplifier": device['id']})
            firebase.child('amplifiers').child(
                device['id']).stream(stream_handler, stream_id=device['id'])
            devices[device['id']] = device['alias']

    client.message_callback_add(
        'gateway/usb-dongle/nodes', handler_device_list)
    client.on_connect = on_connect

    client.connect("localhost")
    client.loop_start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Exited with error: ', e)
        sys.exit(1)
