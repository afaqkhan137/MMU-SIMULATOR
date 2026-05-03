from config_parser import parse_config, calculate_derived_values
from trace_parser import parse_trace
from frame_manager import FrameManager
from mmu import MMU


def main():
    # Get trace file from user
    trace_file = input("Enter trace file path (default: trace_small.txt): ").strip()
    if not trace_file:
        trace_file = "trace_small.txt"

    print("MMU SIMULATOR")

    # Load config
    print("\nLoading configuration...")
    config = parse_config("config.txt")
    config = calculate_derived_values(config)
    config.print_config()

    # Load trace
    print("\nLoading trace file...")
    accesses = parse_trace(trace_file)

    if not accesses:
        print("No valid memory accesses found!")
        return

    all_addresses = [acc.address for acc in accesses]

    # User chooses algorithm
    while True:
        print("\n" + "-" * 40)
        print("   REPLACEMENT ALGORITHM MENU")
        print("-" * 40)
        print("  1. FIFO (First-In-First-Out)")
        print("  2. LRU (Least Recently Used)")
        print("  3. OPT (Optimal - Clairvoyant)")
        print("  0. Exit")
        print("-" * 40)

        try:
            choice = int(input("\nEnter your choice (0-3): "))
        except ValueError:
            print("Invalid input! Please enter a number.")
            continue

        if choice == 0:
            print("\nExiting simulator. Goodbye!")
            break

        if choice == 1:
            algorithm = "FIFO"
        elif choice == 2:
            algorithm = "LRU"
        elif choice == 3:
            algorithm = "OPT"
        else:
            print("Invalid choice! Please enter 0-3.")
            continue

        print(f"\nCreating Frame Manager...")
        fm = FrameManager(config.num_frames)
        fm.print_status()

        print(f"\nMMU using {algorithm} algorithm")

        if algorithm == "OPT":
            mmu = MMU(config, fm, algorithm=algorithm, trace_addresses=all_addresses)
        else:
            mmu = MMU(config, fm, algorithm=algorithm)

        print(f"\nProcessing memory accesses with {algorithm}...")
        print("-" * 60)

        # Reload accesses for each run
        accesses = parse_trace(trace_file)

        for i, acc in enumerate(accesses):
            print(f"\n>>> Access {i+1}/{len(accesses)} <<<")
            phys_addr, latency = mmu.translate(acc.address, acc.is_write)

        mmu.print_stats()


if __name__ == "__main__":
    main()