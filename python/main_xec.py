import asyncio

import requests
import websockets

from chronik_pb2 import Tx, TxHistoryPage, Utxos, ValidateUtxoRequest, ValidateUtxoResponse, Error, OutPoint, \
    Subscription, SubscribeMsg
from python.chronik_pb2 import Block, Blocks


async def main():
    # We can get a single block like this:
    response = requests.get(
        "https://chronik.be.cash/xec/block/00000000000000001567ce04298b71eb26b0904b113a1e4a33c9b3b14ef3b64c"
    )
    block = Block()
    block.ParseFromString(response.content)
    print('fetched', response.request.url)
    print('block timestamp:', block.block_info.timestamp)
    print('block num txs:', len(block.txs))

    # We can get a single block like this:
    response = requests.get(
        "https://chronik.be.cash/xec/block/715980"
    )
    block = Block()
    block.ParseFromString(response.content)
    print('fetched', response.request.url)
    print('block timestamp:', block.block_info.timestamp)
    print('block num txs:', len(block.txs))

    # Block info for a range of blocks:
    response = requests.get(
        "https://chronik.be.cash/xec/blocks/0/100"
    )
    blocks = Blocks()
    blocks.ParseFromString(response.content)
    print('fetched', response.request.url)
    print('num blocks fetched:', len(blocks.blocks))

    # Getting a single tx is very simple.
    # We just call /tx/:txid, and parse the result as Tx message.
    response = requests.get(
        "https://chronik.be.cash/xec/tx/522bd18c84ac52a0e96c986a3850a5527b7a116c42f7f364a137acca8f687e80"
    )
    tx = Tx()
    tx.ParseFromString(response.content)
    print('fetched', response.request.url)
    print('tx block hash:', tx.block.hash[::-1].hex())

    # We get the tx history by calling /script/:script_type/:payload
    # As a result, we get a TxHistoryPage.
    # This will return the txs spending from or sending to the script,
    # with the most recent first.
    response = requests.get(
        "https://chronik.be.cash/xec/script/p2pkh/ccd850bae336c01d2410843f6545ad9ef6d72cab/history"
    )
    history = TxHistoryPage()
    history.ParseFromString(response.content)
    print('fetched', response.request.url)
    print('num tx on page', len(history.txs))

    # Some scripts can have extremely large pages, so we can specify the page.
    # We can also set the page_size if we want a different number of txs per page.
    response = requests.get(
        "https://chronik.be.cash/xec/script/p2pkh/ccd850bae336c01d2410843f6545ad9ef6d72cab/history?page=33&page_size=10"
    )
    history = TxHistoryPage()
    history.ParseFromString(response.content)
    print('fetched', response.request.url)
    print('num tx on page', len(history.txs))

    # We get the UTXOs of a script by calling /script/:script_type/:payload/utxos
    # This gives us all the UTXOs of the script.
    response = requests.get(
        "https://chronik.be.cash/xec/script/p2pkh/ccd850bae336c01d2410843f6545ad9ef6d72cab/utxos"
    )
    utxos = Utxos()
    utxos.ParseFromString(response.content)
    print('fetched', response.request.url)
    print('num of scripts:', len(utxos.script_utxos))
    print('num of utxos:', len(utxos.script_utxos[0].utxos))

    # We can also validate a list of UTXOs by calling /validate-utxos.
    # It expects a list of outpoints and returns whether the output is
    # spent, unspent, or whether the tx/output never existed.
    request = ValidateUtxoRequest()
    request.outpoints.append(utxos.script_utxos[0].utxos[0].outpoint)
    request.outpoints.append(tx.inputs[0].prev_out)
    request.outpoints.append(OutPoint(txid=bytes(32)))
    request_proto = request.SerializeToString()
    response = requests.post(
        "https://chronik.be.cash/xec/validate-utxos",
        request_proto,
        # Removing this results in an error
        headers={"Content-Type": "application/x-protobuf"},
    )
    print(response.request.url, "returned:")
    if response.status_code != 200:
        # We can parse an error like this.
        error = Error()
        error.ParseFromString(response.content)
        print(error)
    else:
        validate_utxos_response = ValidateUtxoResponse()
        validate_utxos_response.ParseFromString(response.content)
        print(validate_utxos_response)

    # We can also listen to updates of scripts via WebSocket by connecting to /ws.
    ws = await websockets.connect("wss://chronik.be.cash/xec/ws")
    # We send a Subscription message to subscribe or unsubscribe.
    msg = Subscription(
        script_type="p2sh",
        # This one is the 2nd address in the coinbase reward list
        payload=bytes.fromhex("260617ebf668c9102f71ce24aba97fcaaf9c666a"),
        is_subscribe=True,
    )
    await ws.send(msg.SerializeToString())
    print('Waiting for txs or confirmations on', msg.payload.hex(), '...')
    while True:
        # We then wait for new txs to that script.
        # Since the address is in the payout, we get a Confirmed message
        # each time we get a new block.
        msg_proto = await ws.recv()
        msg = SubscribeMsg()
        msg.ParseFromString(msg_proto)
        print("New subscription message:")
        print(msg)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
