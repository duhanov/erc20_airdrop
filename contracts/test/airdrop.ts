const Web3 = require("web3");

/* eslint-disable no-undef */
// Right click on the script name and hit "Run" to execute

//const { expect } = require("chai");
//const { ethers } = require("hardhat");

const OldToken = artifacts.require("PancakeIBEP2E");
const NewToken = artifacts.require("NewToken");
const Airdrop = artifacts.require("Airdrop");

contract("Test Airdrop", function (accounts) {
  it("Transfer owner", async function () {
    old_token = await OldToken.deployed();
    new_token = await NewToken.deployed();
    airdrop = await Airdrop.deployed();

    // transfer owner from accounts[0] to contract
    await old_token.transferOwner(airdrop.address);
    // transfer owner back to accounts[0]
    await airdrop.transferContractOwner(old_token.address, accounts[0]);
    // transfer owner from accounts[0] to contract
    await old_token.transferOwner(airdrop.address);
    // transfer owner back to accounts[0]
    await airdrop.transferContractOwner(old_token.address, accounts[0]);
  });

  it("Withdraw tokens", async function () {
    token = await OldToken.deployed();
    airdrop = await Airdrop.deployed();

    const amount = 100;
    // send tokens to contract
    await token.transfer(airdrop.address, amount);
    const balance_before = await token.balanceOf(accounts[0]);
    // return tokens from contract
    await airdrop.withdrawToken(token.address);
    const balance_after = await token.balanceOf(accounts[0]);
    assert.equal(
      balance_before / 1,
      balance_after / 1 - amount,
      "Invalid balance after withdraw"
    );
  });

  it("Airdrop", async function () {
    old_token = await OldToken.deployed();
    new_token = await NewToken.deployed();
    airdrop = await Airdrop.deployed();

    const amount = 100;

    await old_token.transferOwner(airdrop.address);

    // topup old token balance for airdrop
    await old_token.transfer(accounts[1], amount);
    // topup contract new tokens for airdrop
    await new_token.transfer(airdrop.address, amount * 2);

    const balance_before = await new_token.balanceOf(accounts[1]);
    // Make Airdrop
    await airdrop.airdrop(accounts[1], old_token.address, new_token.address);
    const balance_after = await new_token.balanceOf(accounts[1]);
    assert.equal(
      balance_before / 1,
      balance_after / 1 - amount * 2,
      "Invalid new token balance after airdrop"
    );
    const old_token_balance_after = await old_token.balanceOf(accounts[1]);
    //console.log(
    //  "after airdrop:",
    //  (await old_token.balanceOf(accounts[1])) / 1,
    //  (await new_token.balanceOf(accounts[1])) / 1
    //);
    assert.equal(
      old_token_balance_after / 1,
      0,
      "Invalid old token balance after airdrop"
    );

    await airdrop.transferContractOwner(old_token.address, accounts[0]);
  });

  it("Airdrop Zero", async function () {
    old_token = await OldToken.deployed();
    new_token = await NewToken.deployed();
    airdrop = await Airdrop.deployed();

    const amount = 100;

    await old_token.transferOwner(airdrop.address);

    // topup old token balance for airdrop
    await new_token.transfer(airdrop.address, amount * 2);

    const balance_before = await new_token.balanceOf(accounts[1]);
    // Make Airdrop
    await airdrop.airdrop(accounts[1], old_token.address, new_token.address);
    const balance_after = await new_token.balanceOf(accounts[1]);
    assert.equal(
      balance_after / 1,
      balance_before / 1,
      "Invalid new token balance after zero airdrop"
    );
    const old_token_balance_after = await old_token.balanceOf(accounts[1]);
    assert.equal(
      old_token_balance_after / 1,
      0,
      "Invalid old token balance after zero airdrop"
    );

    await airdrop.transferContractOwner(old_token.address, accounts[0]);
  });

  it("Airdrop Cancel", async function () {
    old_token = await OldToken.deployed();
    new_token = await NewToken.deployed();
    airdrop = await Airdrop.deployed();

    const amount = 100;

    // topup old token balance for airdrop
    await old_token.transfer(accounts[1], amount);
    // topup contract new tokens for airdrop
    await new_token.transfer(airdrop.address, amount * 2);

    const new_token_balance_before = await new_token.balanceOf(accounts[1]);
    // Make Airdrop
    try {
      await airdrop.airdrop(accounts[1], old_token.address, new_token.address);
      assert.fail("Airdrop success, but not rights for burn");
    } catch (error) {
      if (!error.message.includes("revert")) {
        assert.fail("Airdrop success, but not rights for burn");
      } else {
        // console.log("airdrop reverted:", error.reason);
      }
    }
    const old_token_balance = await old_token.balanceOf(accounts[1]);
    const new_token_balance = await new_token.balanceOf(accounts[1]);
    const airdrop_balance = await new_token.balanceOf(airdrop.address);
    //    console.log(
    //      "new_balance:",
    //      new_token_balance / 1,
    //      "airdrop:",
    //      airdrop_balance / 1
    //    );
    assert.equal(old_token_balance / 1, amount, "Invalid old token balance");
    assert.equal(
      new_token_balance / 1,
      new_token_balance_before,
      "Invalid new token balance"
    );
  });
});
