const OldToken = artifacts.require("PancakeIBEP2E");
const NewToken = artifacts.require("NewToken");
const Airdrop = artifacts.require("Airdrop");

module.exports = async function (deployer, network, accounts) {
  // тестовый контракт DNT
  if (network === "dev" || network === "test") {
    await deployer.deploy(OldToken);
    const old_token = await OldToken.deployed();
    console.log(`OldToken contract deployed at address: ${old_token.address}`);
    // Предустанавливаем балансы на старом контракте в тестовой сети для тестирования эйрдропа
    console.log("Create balances");
    await old_token.transfer(
      "0x14ef5b599f1CC8F33879E9c3890faE07E96F339c",
      7182701000000,
      { from: accounts[0] }
    );
    await old_token.transfer(
      "0x33Eac50b7fAf4B8842A621d0475335693F5D21fe",
      1997875378183,
      { from: accounts[0] }
    );
    await old_token.transfer(
      "0x3b187e9C972f5777D2BeC4546b679721Cae54Ef9",
      920000,
      {
        from: accounts[0],
      }
    );

    console.log(
      (await old_token.balanceOf(
        "0x14ef5b599f1CC8F33879E9c3890faE07E96F339c"
      )) / 1
    );
  }

  // новый контракт
  await deployer.deploy(NewToken);
  const token = await NewToken.deployed();
  console.log(`NewToken contract deployed at address: ${token.address}`);

  // Контракт аирдропа
  await deployer.deploy(Airdrop);
  const airdrop = await Airdrop.deployed();
  console.log(`Airdrop contract deployed at address: ${airdrop.address}`);
};
