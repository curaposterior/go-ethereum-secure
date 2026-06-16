# go-ethereum-secure

Forked GETH with an implementation that checks whether specific addresses are blacklisted or not.

## Implementation details

The transactions are validated before they are send to the TX pool.

The following files were modified:

* **show_case.py** -> python script that tests the validation logic (uses cast so it requires foundryup project).
* **start_command.sh** -> geth launch script
* **internal/ethapi/blacklist/blacklist.json** -> json file with blacklisted addresses (could be modified when GETH is running, it's pulled everytime that transaction is validated)
* **internal/ethapi/blacklist.go** -> utilities for blacklisting logic
* **internal/ethapi/api.go** -> a check inside the submitTransaction() function that validates transaction before it's send to TX pool and for mining

## Testing

To test it you can launch the show_case.py script in the root directory of this repo (no additional dependencies required other than running GETH and having foundry toolkit available):

```bash
python show_case.py
```
