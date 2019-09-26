// Require the Helix libraries
// You obviously need the pendulum sdk to this script
//
//
const HELIX = require("@helixnetwork/core");

const CONVERTER = require("@helixnetwork/converter");

const HELIX_COMPOSER = HELIX.composeAPI({
  provider: "http://localhost:8085"
});

const DEPTH = 5;

const MINWEIGHTMAGNITUDE = 2;

const SENDER_SEED =
  "";

var sender_initial_value = 536561674354688;

const AMOUNT_TO_SEND = 1;

const RECEIVER_SEED =
  "abc01234abc01234abc01234abc01234abc01234abc01234abc01234abc01234";

const SECURITY_LEVEL = 2;

const CHECKSUM = false;

// periodicity is the interval length in miliseconds between sending
const PERIODICITY = 30000;

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function spam_value(){
  var inputs = {
    address: "",
    keyIndex: 0,
    security: SECURITY_LEVEL,
    balance: sender_initial_value
  };

  var remainder_address = "";

  var transfers = {
    address: "",
    value: 0,
    message: CONVERTER.asciiToTxHex("magic"),
    tag: CONVERTER.asciiToTxHex("magic")
  };

  var options = {
      security: SECURITY_LEVEL,
      inputs: "",
      remainderAddress: ""
  };

  for (let i = 1; i < 1000000000; i++) {
    var address_index = i;
    var stored_tx_bytes;
    if (sender_initial_value > AMOUNT_TO_SEND) {

      transfers.value = AMOUNT_TO_SEND;
      transfers.address = HELIX.generateAddress(
        RECEIVER_SEED, address_index, SECURITY_LEVEL, CHECKSUM
      );

      inputs.keyIndex = address_index;
      inputs.balance = sender_initial_value;
      inputs.address = HELIX.generateAddress(
        SENDER_SEED, address_index, SECURITY_LEVEL, CHECKSUM
      );

      options.inputs = inputs;
      options.remainderAddress = HELIX.generateAddress(
        SENDER_SEED, address_index+1, SECURITY_LEVEL, CHECKSUM
      );// remainderAddress


      HELIX_COMPOSER.prepareTransfers(SENDER_SEED, [transfers], options)
        .then(function(tx_bytes) {
          stored_tx_bytes = tx_bytes;
          return HELIX_COMPOSER.sendTransactionStrings(
            stored_tx_bytes,
            DEPTH,
            MINWEIGHTMAGNITUDE
          );
        })
        .then(results => //console.log(JSON.stringify(results))
          console.log(
            "Sent", AMOUNT_TO_SEND,
            "from address", results[1].address,
            "to address", results[0].address,
            "\nChange address", results[2].address,
            "now has", results[2].value, "\n"
          )
        )
        .catch(err => {
          console.log(err);
        });
    }
    else {
      console.log("Finished sending!");
    }
    sender_initial_value -= AMOUNT_TO_SEND;
    await sleep(PERIODICITY);
  }
};

spam_value();
