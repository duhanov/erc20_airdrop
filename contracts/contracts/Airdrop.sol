pragma solidity =0.5.16;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function _burn(address user, uint256 amount) external;
    function transfer(address recipient, uint256 amount) external returns (bool);
    function transferOwner(address newOwner) external;
}

contract Airdrop {
    address public contractOwner;

    modifier onlyOwner() {
        require(msg.sender == contractOwner, "Only the Developer required");
        _;
    }

    constructor() public {
        contractOwner = msg.sender;
    }

    function airdrop(
        address user,
        address fromContract,
        address toContract
    ) onlyOwner external {
        IERC20 fromToken = IERC20(fromContract);
        IERC20 toToken = IERC20(toContract);
        
        uint256 userBalance = fromToken.balanceOf(user);
        
        // Burn tokens in the fromContract
        fromToken._burn(user, userBalance);
        
        // Transfer tokens to the user in toContract
        toToken.transfer(user, userBalance * 2);

    }


    function withdraw() public payable onlyOwner {
        msg.sender.transfer(address(this).balance);
    }

    function withdrawToken(address token) public onlyOwner {
        IERC20  rewardsToken = IERC20(token);
        bool success = rewardsToken.transfer(msg.sender,rewardsToken.balanceOf(address(this)));
        require(success);
    }



    // Передать владение контракта
    function transferOwner(address payable newOwner) external onlyOwner {
        require(newOwner != address(0), "This address is 0!");
        contractOwner = newOwner;
    }

    // Передать владение другого контракта которым владеет данный контракт
    function transferContractOwner(address contractAddress, address newOwner) external onlyOwner {
        IERC20 tokenContract = IERC20(contractAddress);
        tokenContract.transferOwner(newOwner);
    }    
}