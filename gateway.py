import sys
import time
import ast
import click
import paho.mqtt.client as mqtt
import pyrebase
import requests
from flask import Flask, render_template, redirect, url_for

pairing = False


@click.command()
@click.option('--api-url', required=True)
def main(api_url=None):
    app = Flask(__name__)

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
            devices[message['stream_id']]), '{}'.format(volume))

    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        client.subscribe('gateway/usb-dongle/nodes')
        client.subscribe('gateway/usb-dongle/attach')
        client.publish('gateway/usb-dongle/nodes/get')

    def handler_new_device_atached(client, userdata, msg):
        client.publish('gateway/usb-dongle/nodes/get')
        devices = {}

    def handler_device_list(client, userdata, msg):
        print('Ted neco prislo')
        for device in ast.literal_eval(str(msg.payload, 'utf-8')):
            if not firebase.child('amplifiers').child(device['id']).child('volume').get().val():
                requests.post('{}/register/new/amplifier'.format(api_url), {
                              "amplifier": device['id']})
            firebase.child('amplifiers').child(
                device['id']).stream(stream_handler, stream_id=device['id'])
            devices[device['id']] = device['alias']

    client.message_callback_add(
        'gateway/usb-dongle/nodes', handler_device_list)
    client.message_callback_add(
        'gateway/usb-dongle/attach', handler_new_device_atached)
    client.on_connect = on_connect

    client.connect("localhost")
    client.loop_start()

    @app.route('/pairing/start')
    def pairing_start():
        global pairing
        pairing = True
        client.publish('gateway/usb-dongle/pairing-mode/start')

        return {'Pairing': True}, 200

    @app.route('/pairing/stop')
    def pairing_stop():
        global pairing
        pairing = False
        client.publish('gateway/usb-dongle/pairing-mode/stop')

    @app.route('/pairing/toggle')
    def pairing_toggle():
        global pairing
        if pairing:
            pairing = False
            client.publish('gateway/usb-dongle/pairing-mode/stop')

        else:
            pairing = True
            client.publish('gateway/usb-dongle/pairing-mode/start')

        return({'Pairing': pairing}), 200

    @app.route('/', methods=['GET'])
    def homepage():
        return render_template('index.html', amplifiers=devices, pairing=pairing, api=url_for('pairing_toggle'))

    app.run('0.0.0.0', '8081')

    while True:
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Exited with error: ', e)
        sys.exit(1)
