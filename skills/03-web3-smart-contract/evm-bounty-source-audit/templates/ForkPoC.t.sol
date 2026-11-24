// SPDX-License-Identifier: SEL-1.0
// Fork-PoC starter for EVM bug-bounty audits. Copy to <project>/test/ForkPoC.t.sol and fill in.
//
// Run against a LOCAL FORK (never interact with the live deployment directly):
//   export FORK_RPC="https://ethereum-rpc.publicnode.com"
//   forge test --match-contract ForkPoC -vv
//   RUN_TEMPLATE=true forge test --match-test test_TEMPLATE_impact -vvvv
//
// Requires in foundry.toml:  fs_permissions = [{ access = "read", path = "./" }]
// and forge-std living in THIS project's own lib/ (Foundry refuses sources outside the project root).
//
// cluster.json shape next to the project root:
//   {"cluster": {"vault": "0x..", "teller": "0x..", "queue": "0x..", "manager": "0x..", "accountant": "0x.."}}
// IMPORTANT: teller must be the value read from vault.hook() on chain — deployment records go stale
// (they can disagree in address AND in params like shareLockPeriod).
//
// Before filling this in, read the skill's references/evm-live-recon-and-fork-harness.md:
// funds-at-risk sweep, approve-the-real-puller, quote==execution asserts, cast-parsing pitfalls.
pragma solidity 0.8.21;

import {Test, console2} from "forge-std/Test.sol";

interface IERC20Like {
    function balanceOf(address) external view returns (uint256);
    function totalSupply() external view returns (uint256);
    function decimals() external view returns (uint8);
    function symbol() external view returns (string memory);
}
interface IBoringVaultLike {
    function hook() external view returns (address);
    function authority() external view returns (address);
    function owner() external view returns (address);
    function totalSupply() external view returns (uint256);
}
interface ITellerLike {
    function vault() external view returns (address);
    function accountant() external view returns (address);
    function shareLockPeriod() external view returns (uint64);
    function isPaused() external view returns (bool);
}
interface IQueueLike {
    function boringVault() external view returns (address);
    function isPaused() external view returns (bool);
}
interface IManagerLike {
    function vault() external view returns (address);
    function manageRoot(address strategist) external view returns (bytes32);
}
interface IAccountantLike {
    function vault() external view returns (address);
    function getRate() external view returns (uint256);
}
interface IRolesAuthorityLike {
    function isCapabilityPublic(address target, bytes4 selector) external view returns (bool);
    function canCall(address user, address target, bytes4 selector) external view returns (bool);
}

contract ForkPoC is Test {
    string constant CLUSTER_JSON = "./cluster.json";

    address vault;
    address teller;
    address queue;
    address manager;
    address accountant;
    address authority;

    address attacker = address(0xA11CE);

    function setUp() public {
        string memory rpc = vm.envOr("FORK_RPC", string("https://ethereum-rpc.publicnode.com"));
        vm.createSelectFork(rpc);
        // For reproducibility pin the block: vm.createSelectFork(rpc, 21_000_000);

        string memory j = vm.readFile(CLUSTER_JSON);
        vault = vm.parseJsonAddress(j, ".cluster.vault");
        teller = vm.parseJsonAddress(j, ".cluster.teller");
        queue = vm.parseJsonAddress(j, ".cluster.queue");
        manager = vm.parseJsonAddress(j, ".cluster.manager");
        accountant = vm.parseJsonAddress(j, ".cluster.accountant");
        authority = IBoringVaultLike(vault).authority();
    }

    // 1) Every cluster member must point at the SAME vault; teller == live hook.
    function test_clusterWiring() public view {
        assertEq(IBoringVaultLike(vault).hook(), teller, "vault.hook != teller");
        assertEq(ITellerLike(teller).vault(), vault, "teller.vault != vault");
        assertEq(IQueueLike(queue).boringVault(), vault, "queue.boringVault != vault");
        assertEq(IManagerLike(manager).vault(), vault, "manager.vault != vault");
        assertEq(IAccountantLike(accountant).vault(), vault, "accountant.vault != vault");
    }

    // 2) Live snapshot: the numbers the report will quote.
    function test_snapshot() public view {
        console2.log("vault", vault);
        console2.log("  symbol", IERC20Like(vault).symbol());
        console2.log("  totalSupply", IERC20Like(vault).totalSupply());
        console2.log("  authority", authority);
        console2.log("teller", teller);
        console2.log("  shareLockPeriod", ITellerLike(teller).shareLockPeriod());
        console2.log("  paused", ITellerLike(teller).isPaused());
        console2.log("queue share balance", IERC20Like(vault).balanceOf(queue));
        console2.log("accountant rate", IAccountantLike(accountant).getRate());
    }

    // 3) Capability probe convention: ask the TARGET contract's OWN authority.
    //    Sanity-check any all-false sweep with a selector the deployment config marks public.
    function test_capability_probe() public view {
        address probe = address(0xBAD);
        assertFalse(
            IRolesAuthorityLike(authority).canCall(probe, teller, bytes4(keccak256("deposit(address,uint256,uint256,address)"))),
            "unprivileged attacker holds teller.deposit"
        );
    }

    // 4) TEMPLATE — the actual exploit. Enable with RUN_TEMPLATE=true once a candidate finding exists.
    function test_TEMPLATE_impact() public {
        if (!vm.envOr("RUN_TEMPLATE", false)) {
            vm.skip(true);
        }

        // ---- 1. PRE-CONDITIONS: prove the attacker is unprivileged (canCall == false) ----
        assertFalse(
            IRolesAuthorityLike(authority).canCall(attacker, teller, bytes4(keccak256("deposit(address,uint256,uint256,address)"))),
            "attacker privileged"
        );

        // ---- 2. MAIN: execute the exploit as the attacker ----
        vm.startPrank(attacker);
        // <exploit calls>
        vm.stopPrank();

        // ---- 3. IMPACT: assert value actually moved (attacker gain, vault/totalSupply loss) ----
        // assertGt(<attacker gain>, 0, "no gain");

        // ---- 4. CONTROL arm: run the same sequence with the bug's precondition removed
        //         (e.g. vm.store the guard/lock back) and show the attacker does NOT profit there.
        //         Only the MAIN-vs-CONTROL difference carries the report; a lone "profit" is an
        //         accounting artifact until the control proves the precondition is what enabled it.

        console2.log("attacker", attacker);
        console2.log("vault", vault);
        console2.log("teller", teller);
    }
}
