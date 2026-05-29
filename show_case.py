import os
import subprocess
import tempfile
from dataclasses import dataclass
import json


GETH_CONNECTION_STRING = "http://127.0.0.1:8545"


@dataclass
class TestAccount:
    name: str
    priv_key: str
    pub_key: str
    balance: str = "0"
    can_receive: bool = True
    can_send: bool = True

    def _present_account(self):
        print()
        print(f"Account: {self.name}")
        print(f"Pub_key={self.pub_key}, priv_key={self.priv_key}")
        print(f"Privileges: can_receive={self.can_receive}, can_send={self.can_send}", "\n")


class Blacklist:
    def __init__(self, path: str = './internal/ethapi/blacklist/blacklist.json'):
        self.path_to_blacklist: str = path
        self.blacklisted_recipients = []
        self.blacklisted_senders = []
        self._populate_blacklisted_addresses()
    
    def _populate_blacklisted_addresses(self):
        with open(self.path_to_blacklist, 'r') as f:
            data = json.load(f)
        self.blacklisted_senders = data["addresses"]["senders"]
        self.blacklisted_recipients = data["addresses"]["recipients"]

    def _blacklist_sender(self, address: str):
        with open(self.path_to_blacklist, 'r') as f:
            data = json.load(f)
        if address in data["addresses"]["senders"]:
            print("Address already in the file")
            return
        data["addresses"]["senders"].append(address)
        with open(self.path_to_blacklist, 'w') as f:
            json.dump(data, f, indent=4)
        self.blacklisted_senders.append(address)

    def _blacklist_recipient(self, address: str) -> None:
        with open(self.path_to_blacklist, 'r') as f:
            data = json.load(f)
        if address in data["addresses"]["recipients"]:
            print("Address already in the file")
            return
        data["addresses"]["recipients"].append(address)
        with open(self.path_to_blacklist, 'w') as f:
            json.dump(data, f, indent=4)
        self.blacklisted_recipients.append(address)


def extract_private_key_via_pub(pub_key: str) -> str:
    keystore_dir = './dev-chain/keystore'
    pub_key_lower = pub_key.lower().removeprefix('0x')
    keystore_file = None
    for fname in os.listdir(keystore_dir):
        if fname.lower().endswith(pub_key_lower):
            keystore_file = os.path.join(keystore_dir, fname)
            break
    if keystore_file is None:
        raise FileNotFoundError(f"No keystore file found for address {pub_key}")

    result = subprocess.run(
        ['cast', 'wallet', 'decrypt-keystore', '--unsafe-password', '', '--keystore-dir', './', keystore_file],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    for line in output.splitlines():
        if 'private key is:' in line:
            return line.split('private key is:')[-1].strip()
    raise RuntimeError(f"Could not extract private key:\n{output}")


def create_test_account(name: str) -> TestAccount:
    result = subprocess.run(
        ['./build/bin/geth', '--datadir', './dev-chain', 'account', 'new'],
        capture_output=True,
        input='\n\n',
        text=True,
    )

    output = result.stdout + result.stderr
    pub_key = None
    keystore_path = None
    for line in output.splitlines():
        if 'Public address of the key:' in line:
            pub_key = line.split(':', 1)[-1].strip()
        elif 'Path of the secret key file:' in line:
            keystore_path = line.split(':', 1)[-1].strip()
    if not pub_key or not keystore_path:
        raise RuntimeError(f"Could not parse geth output:\n{output}")

    priv_key = extract_private_key_via_pub(pub_key)
    return TestAccount(name=name, priv_key=priv_key.lower(), pub_key=pub_key.lower(), balance='0')


def send_transaction(_from: TestAccount, _to: TestAccount, value: str) -> bool:
    print(f"\n[TX] {_from.name} ({_from.pub_key}) -> {_to.name} ({_to.pub_key}) value={value}")
    result = subprocess.run(
        [
            'cast', 'send',
            _to.pub_key,
            '--value', value,
            '--rpc-url', GETH_CONNECTION_STRING,
            '--private-key', _from.priv_key,
            '--json',
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        try:
            tx_hash = json.loads(result.stdout).get('transactionHash', '?')
        except (json.JSONDecodeError, AttributeError):
            tx_hash = '?'
        print(f"[TX] accepted tx_hash={tx_hash}")
        return True
    else:
        error = (result.stderr or result.stdout).strip()
        print(f"[TX] rejected {error}")
        return False


def main(blacklist: Blacklist):
    dead_account = TestAccount(
        "dead",
        "",
        "0x000000000000000000000000000000000000dEaD",
        can_send=False,
    )
    starting_account = TestAccount(
        "big_money",
        extract_private_key_via_pub("0x71562b71999873db5b286df957af199ec94617f7"),
        "0x71562b71999873db5b286df957af199ec94617f7",
        can_receive=False,
    )
    dead_account._present_account()
    starting_account._present_account()

    test_1 = create_test_account("test1")
    test_1._present_account()
    test_2 = create_test_account("test2")
    test_2.can_send = False
    test_2._present_account()

    print("="*40)
    print("TESTING TRANSATIONS")
    print("="*40)

    print(f"Blacklisting: {starting_account.pub_key} and {test_2.pub_key}")
    blacklist._blacklist_recipient(starting_account.pub_key)
    blacklist._blacklist_sender(test_2.pub_key)
    input()
    send_transaction(starting_account, test_1, "0.2ether")
    input()
    send_transaction(starting_account, test_2, "2ether")
    input()
    send_transaction(test_1, starting_account, "1wei")
    input()
    send_transaction(test_2, test_1, "2wei")
    input()


if __name__ == "__main__":
    black = Blacklist()
    main(black)
