### Linux Setup Instructions

**NOTE**: It is advised to have at least 20GB of available disk space to allow Chronik to sync properly (disk usage will grow and shrink during sync time)

1. Download and extract latest Lotus: https://storage.googleapis.com/lotus-project/lotus-2.1.3-x86_64-linux-gnu.tar.gz
2. Add a file named `lotus.conf` to the appropriate datadir with the following contents:
  ```
  # Main
  listen=1
  server=1
  txindex=1
  disablewallet=1
  # RPC
  rpcuser=lotus
  rpcpassword=lotus
  rpcbind=127.0.0.1
  rpcworkqueue=10000
  rpcthreads=8
  # Chronik
  nngpub=ipc:///path/to/pub.pipe
  nngrpc=ipc://path/to/rpc.pipe
  nngpubmsg=blkconnected
  nngpubmsg=blkdisconctd
  nngpubmsg=mempooltxadd
  nngpubmsg=mempooltxrem
  ```
**IMPORTANT**: Be sure to set real file paths for `nngpub` and `nngrpc`; Example: `nngpub=ipc:///var/lib/chronik/pub.pipe`

3. Download latest Chronik binary: https://d.be.cash/chronik-0.1.1-x86_64-linux-gnu
4. Create new `chronik.conf` in same dir as Chronik binary with the following contents:
  ```
  host = "127.0.0.1:7123"
  nng_pub_url = "ipc:///path/to/pub.pipe"
  nng_rpc_url = "ipc:///path/to/rpc.pipe"
  db_path = "/path/to/index.rocksdb"
  cache_script_history = 100000
  network = "XPI"
  [bitcoind_rpc]
  url = "http://127.0.0.1:10604"
  rpc_user = "lotus"
  rpc_pass = "lotus"
  ```
**IMPORTANT**: Be sure to set your `nng_pub_url` and `nng_rpc_url` according to your `lotus.conf`

5. Launch Lotus node and await full sync
6. Open a terminal to the dir with the Chronik binary, then make the binary executable:
  ```
  chmod +x chronik-0.1.1.-x86_64-linux-gnu
  ```
7. Run Chronik:
  ```
  ./chronik-0.1.1.-x86_64-linux-gnu chronik.conf
  ```

If everything is working correctly, you should begin seeing "`Added block ...`" lines scrolling through the terminal window

In your `chronik.conf` file, feel free to adjust the `host` parameter to your liking. This is the IP address and port that Chronik will bind to for inbound connections
