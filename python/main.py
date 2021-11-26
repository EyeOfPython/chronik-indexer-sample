import asyncio

import requests
import websockets

from chronik_pb2 import Tx, TxHistoryPage, Utxos, ValidateUtxoRequest, ValidateUtxoResponse, Error, OutPoint, \
    Subscription, SubscribeMsg


async def main():
    # Getting a single tx is very simple.
    # We just call /tx/:txid, and parse the result as Tx message.
    response = requests.get(
        "https://chronik.be.cash/xpi/tx/00c974a479a139b0b3773fca91bc7bd24e7ab53273e836d049455c1049f34c07"
    )
    tx = Tx()
    tx.ParseFromString(response.content)
    print(response.request.url, "returned:")
    print(tx)

    # We get the tx history by calling /script/:script_type/:payload
    # As a result, we get a TxHistoryPage.
    # This will return the txs spending from or sending to the script,
    # with the most recent first.
    response = requests.get(
        "https://chronik.be.cash/xpi/script/p2pkh/80cd77837f0d987e88da513405e0c0918652feac/history"
    )
    history = TxHistoryPage()
    history.ParseFromString(response.content)
    print(response.request.url, "returned:")
    print(history)

    # Some scripts can have extremely large pages, so we can specify the page.
    # We can also set the page_size if we want a different number of txs per page.
    response = requests.get(
        "https://chronik.be.cash/xpi/script/p2pkh/b8ae1c47effb58f72f7bca819fe7fc252f9e852e/history?page=33&page_size=10"
    )
    history = TxHistoryPage()
    history.ParseFromString(response.content)
    print(response.request.url, "returned:")
    print(history)

    # We get the UTXOs of a script by calling /script/:script_type/:payload/utxos
    # This gives us all the UTXOs of the script.
    response = requests.get(
        "https://chronik.be.cash/xpi/script/p2pkh/80cd77837f0d987e88da513405e0c0918652feac/utxos"
    )
    utxos = Utxos()
    utxos.ParseFromString(response.content)
    print(response.request.url, "returned:")
    print(utxos)

    # We can also validate a list of UTXOs by calling /validate-utxos.
    # It expects a list of outpoints and returns whether the output is
    # spent, unspent, or whether the tx/output never existed.
    request = ValidateUtxoRequest()
    request.outpoints.append(utxos.utxos[0].outpoint)
    request.outpoints.append(tx.inputs[0].prev_out)
    request.outpoints.append(OutPoint(txid=bytes(32)))
    request_proto = request.SerializeToString()
    response = requests.post(
        "https://chronik.be.cash/xpi/validate-utxos",
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
    ws = await websockets.connect("wss://chronik.be.cash/xpi/ws")
    # We send a Subscription message to subscribe or unsubscribe.
    msg = Subscription(
        script_type="p2pkh",
        # This one is the 2nd address in the coinbase reward list
        payload=bytes.fromhex("b8ae1c47effb58f72f7bca819fe7fc252f9e852e"),
        is_subscribe=True,
    )
    await ws.send(msg.SerializeToString())
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
