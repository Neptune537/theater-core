import json
import math
import time

import websocket
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

with open('../../heavenlyBound/dist/sonar-config.json', encoding='utf-8-sig') as source:
    config = json.load(source)
key = Ed25519PublicKey.from_public_bytes(
    bytes.fromhex(config['publisher_keys']['did:atlantis:seed-radio']))

for origin in ('https://play.tr7n7t7.com', 'https://lite.tr7n7t7.com'):
    ws = websocket.create_connection(config['endpoints'][0], origin=origin,
                                     subprotocols=['sonar.v1'], timeout=10)
    try:
        ws.send(json.dumps({'action': 'subscribe', 'topic': 'gyre:sonar:tactical'}))
        event = json.loads(ws.recv())['event']
        message = event['payload']['message']
        key.verify(bytes.fromhex(event['signature']), message.encode())
        update = json.loads(message)
        entity = update['entity']
        print(json.dumps({
            'origin': origin,
            'entity_id': entity['entity_id'],
            'bounty_cyan': entity['attached_bounty_cyan'],
            'ecef_radius_km': round(math.hypot(*entity['ecef']) / 1000, 1),
            'age_ms': int(time.time() * 1000) - update['observed_at_unix_ms'],
            'signature_valid': True,
        }))
    finally:
        ws.close()
