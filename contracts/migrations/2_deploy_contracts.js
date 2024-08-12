const fs = require("fs");
const path = require("path");

const OldToken = artifacts.require("OldPancakeIBEP2E");
const NewToken = artifacts.require("PancakeIBEP2E");
const Airdrop = artifacts.require("Airdrop");

module.exports = async function (deployer, network, accounts) {
  let envs = {};

  // Контракт аирдропа
  await deployer.deploy(Airdrop);
  const airdrop = await Airdrop.deployed();
  console.log(`Airdrop contract deployed at address: ${airdrop.address}`);
  envs["AIRDROP_CONTRACT"] = airdrop.address;
  // новый контракт
  await deployer.deploy(NewToken);
  const new_token = await NewToken.deployed();
  console.log(`NewToken contract deployed at address: ${new_token.address}`);
  envs["NEW_TOKEN_CONTRACT"] = new_token.address;
  // тестовый контракт DNT
  if (
    network === "dev" ||
    network === "dev_test" ||
    network === "test" ||
    network === "prod_test"
  ) {
    await deployer.deploy(OldToken);
    const old_token = await OldToken.deployed();
    console.log(`OldToken contract deployed at address: ${old_token.address}`);
    envs["OLD_TOKEN_CONTRACT"] = old_token.address;
    // Предустанавливаем балансы на старом контракте в тестовой сети для тестирования эйрдропа
    console.log("Create balances");

    let transfers = [
      { to: "0x814feFD110dFb582ce47FCF120A6feBe907D6134", amount: 19978753781 },
      //      { to: "0x14ef5b599f1CC8F33879E9c3890faE07E96F339c", amount: 71827010000 },
      { to: "0x33Eac50b7fAf4B8842A621d0475335693F5D21fe", amount: 19978753781 },
      { to: "0x3b187e9C972f5777D2BeC4546b679721Cae54Ef9", amount: 920000 },
    ];
    if (network === "prod_test") {
      transfers = [
        {
          to: "0x14ef5b599f1CC8F33879E9c3890faE07E96F339c",
          amount: 71827010000,
        },
      ];
    }
    for (const transfer of transfers) {
      await old_token.transfer(transfer.to, transfer.amount, {
        from: accounts[0],
      });
    }
    //  Пополняем контракт для тестирования airdrop

    const total_amount = transfers.reduce(
      (acc, transfer) => acc + transfer.amount,
      0
    );
    console.log(
      "Transfer ",
      total_amount * 2,
      " new tokens to",
      airdrop.address
    );
    await new_token.transfer(airdrop.address, total_amount * 2);
    console.log(
      "contract balance: ",
      (await new_token.balanceOf(airdrop.address)) / 1
    );
  }

  const envFilePath = path.resolve(__dirname, "../../.env");
  console.log("save ", envFilePath);
  const envContent = Object.entries(envs)
    .map(([key, value]) => `${key}=${value}`)
    .join("\n");

  fs.writeFileSync(envFilePath, envContent);
};
