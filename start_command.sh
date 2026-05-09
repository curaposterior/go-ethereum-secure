#!/bin/bash
make geth

./build/bin/geth \
  --dev \
  --http \
  --http.addr 127.0.0.1 \
  --http.port 8545 \
  --http.api eth,net,web3,txpool,debug \
  --datadir ./dev-chain
