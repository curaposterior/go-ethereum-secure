package ethapi

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/ethereum/go-ethereum/log"
)

type BlacklistedAddress struct {
	Addresses struct {
		Senders    []string `json:"senders"`
		Recipients []string `json:"recipients"`
	} `json:"addresses"`
}

func arrContains(sl []string, name string) bool {
	for _, value := range sl {
		if strings.EqualFold(value, name) {
			return true
		}
	}
	return false
}

func ReadBlacklistedAddresses(path string) BlacklistedAddress {
	data, err := os.ReadFile(path)
	if err != nil {
		panic(err)
	}

	var addresses BlacklistedAddress
	if err := json.Unmarshal(data, &addresses); err != nil {
		panic(err)
	}
	return addresses
}

func CheckIfBlacklisted(from string, to string) error {
	var blacklist BlacklistedAddress = ReadBlacklistedAddresses("internal/ethapi/blacklist/blacklist.json")

	// check if from in blacklist
	if arrContains(blacklist.Addresses.Senders, from) {
		log.Error("Sender address from", from, "present in blacklist")
		return fmt.Errorf("Sender address 'from' %s is blacklisted", from)
	}

	// check if to in blacklist
	if arrContains(blacklist.Addresses.Recipients, to) {
		log.Error("Recipient address 'to'", to, "present in blacklist")
		return fmt.Errorf("Recipient address 'to' %s is blacklisted", to)
	}

	return nil
}
