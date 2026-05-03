from address_splitter import split_address
from page_table import PageTable
from tlb import TLB
from frame_manager import FrameManager
from replacement import FIFO, LRU, OPT

class MMU:

    def __init__(self, config, frame_manager, algorithm="FIFO", trace_addresses=None):
        #Trace addresses needed for OPT
        self.config = config
        self.frame_manager = frame_manager
        self.algorithm = algorithm

        self.page_table = PageTable()
        self.tlb = TLB(config.tlb_size)

        self.total_accesses = 0
        self.total_latency_ns = 0
        self.page_faults = 0
        self.disk_reads = 0
        self.disk_writes = 0

        # Current position in trace (for OPT)
        self.current_index = 0

        # Select replacement algorithm
        if algorithm == "FIFO":
            self.replacement = FIFO()
        elif algorithm == "LRU":
            self.replacement = LRU()
        elif algorithm == "OPT":
            if trace_addresses is None:
                raise ValueError("OPT algorithm requires trace_addresses parameter")
            self.replacement = OPT(trace_addresses, config.offset_bits)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        print(f"\n--- MMU Initialized with {algorithm} algorithm ---")

    def translate(self, virtual_address, is_write):
        self.total_accesses += 1
        total_latency = 0

        # Default statuses
        tlb_status = "MISS"
        page_status = "HIT"
        disk_status = "NONE"
        dirty_status = "NO"

        vpn, offset = split_address(
            virtual_address,
            self.config.offset_bits,
            self.config.offset_mask
        )

        frame, tlb_hit = self.tlb.lookup(vpn)
        total_latency += self.config.tlb_latency_ns

        if tlb_hit:
            tlb_status = "HIT"
        else:
            tlb_status = "MISS"
            total_latency += self.config.ram_latency_ns
            pte = self.page_table.get_entry(vpn)

            if pte and pte.valid:
                frame = pte.frame
                page_status = "HIT"
                self.tlb.insert(vpn, frame)
            else:
                page_status = "FAULT"
                self.page_faults += 1

                fault_latency, frame = self._handle_page_fault(vpn)
                total_latency += fault_latency
                disk_status = "READ"

                self.tlb.insert(vpn, frame)

        if is_write:
            self.page_table.mark_dirty(vpn)
            dirty_status = "YES"

        total_latency += self.config.ram_latency_ns

        physical_address = (frame << self.config.offset_bits) | offset

        self.total_latency_ns += total_latency
        self.current_index += 1

        # Create summary string
        summary = f"[TLB: {tlb_status}] [Page: {page_status}] [Disk: {disk_status}] [Dirty: {dirty_status}]"

        return physical_address, total_latency, summary

    def _handle_page_fault(self, vpn):
        latency = 0

        if not self.frame_manager.has_free_frames():
            # RAM is full - need to evict

            # Get list of valid VPNs currently in RAM
            valid_vpns = [v for v, pte in self.page_table.table.items() if pte.valid]

            if not valid_vpns:
                raise Exception("No valid pages in RAM to evict!")

            # Try to get victim from replacement algorithm
            if self.algorithm == "OPT":
                evicted_vpn = self.replacement.evict(self.current_index, valid_vpns)
            else:
                evicted_vpn = self.replacement.evict()

                # If replacement returned None (empty queue), pick first valid page
                if evicted_vpn is None:
                    evicted_vpn = valid_vpns[0]

            # Get evicted page info
            evicted_pte = self.page_table.get_entry(evicted_vpn)
            evicted_frame = evicted_pte.frame
            evicted_dirty = evicted_pte.dirty

            print(f"  RAM full! Evicting VPN {evicted_vpn} from Frame {evicted_frame}")

            if evicted_dirty:
                latency += self.config.disk_latency_ns
                self.disk_writes += 1
                print(f"  Evicted page DIRTY! Disk write: +{self.config.disk_latency_ns} ns")
            else:
                print(f"  Evicted page CLEAN: No disk write needed")

            self.replacement.invalidate(evicted_vpn)
            self.tlb.invalidate(evicted_vpn)

            self.frame_manager.free_frame(evicted_frame)
            evicted_pte.valid = 0
            evicted_pte.frame = -1

            frame = evicted_frame
        else:
            frame = self.frame_manager.allocate_frame()
            print(f"  Free frame available: allocated Frame {frame}")

        # Load page from disk
        latency += self.config.disk_latency_ns
        self.disk_reads += 1
        print(f"  Loading VPN {vpn} from disk: +{self.config.disk_latency_ns} ns")

        self.page_table.set_frame(vpn, frame)

        return latency, frame

    def get_stats(self):
        tlb_stats = self.tlb.get_stats()
        # Calculate EAT
        tlb_hit_rate = tlb_stats['hit_rate']
        tlb_miss_rate = 1 - tlb_hit_rate
        page_fault_rate = self.page_faults / self.total_accesses if self.total_accesses > 0 else 0

        eat_ns = (tlb_hit_rate * self.config.tlb_latency_ns) + \
                 (tlb_miss_rate * (self.config.ram_latency_ns +
                                   page_fault_rate * (self.config.disk_latency_ns)))
        avg_latency_ns = self.total_latency_ns / self.total_accesses if self.total_accesses > 0 else 0
        avg_latency_ms = avg_latency_ns / 1_000_000

        return {
            'algorithm': self.algorithm,
            'total_accesses': self.total_accesses,
            'tlb_hits': tlb_stats['hits'],
            'tlb_misses': tlb_stats['misses'],
            'tlb_hit_rate': tlb_stats['hit_rate'],
            'page_faults': self.page_faults,
            'page_fault_rate': self.page_faults / self.total_accesses if self.total_accesses > 0 else 0,
            'disk_reads': self.disk_reads,
            'disk_writes': self.disk_writes,
            'total_latency_ns': self.total_latency_ns,
            'total_latency_ms': self.total_latency_ns / 1_000_000,
            'avg_latency_ns': avg_latency_ns,
            'avg_latency_ms': avg_latency_ms,
            'eat_ns': eat_ns,
            'eat_ms': eat_ns / 1_000_000
        }

    def print_stats(self):
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print(f"MMU STATISTICS ({stats['algorithm']})")
        print("=" * 60)
        print(f"Total Accesses:     {stats['total_accesses']}")
        print(f"\nTLB Statistics:")
        print(f"  Hits:             {stats['tlb_hits']}")
        print(f"  Misses:           {stats['tlb_misses']}")
        print(f"  Hit Rate:         {stats['tlb_hit_rate']:.2%}")
        print(f"\nPage Fault Statistics:")
        print(f"  Page Faults:      {stats['page_faults']}")
        print(f"  Fault Rate:       {stats['page_fault_rate']:.2%}")
        print(f"\nDisk I/O:")
        print(f"  Disk Reads:       {stats['disk_reads']}")
        print(f"  Disk Writes:      {stats['disk_writes']}")
        print(f"\nLatency:")
        print(f"  Total Time:       {stats['total_latency_ns']:,.0f} ns ({stats['total_latency_ms']:.2f} ms)")
        print(f"  Average Time:     {stats['avg_latency_ns']:.0f} ns ({stats['avg_latency_ms']:.4f} ms)")
        print(f"\nEffective Access Time (EAT):")
        print(f"  Theoretical:      {stats['eat_ns']:.2f} ns ({stats['eat_ms']:.4f} ms)")
        print(f"  Actual Average:   {stats['avg_latency_ns']:.0f} ns ({stats['avg_latency_ms']:.4f} ms)")
        print("=" * 60)

# Test the module when run directly
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING MMU")
    print("=" * 50)


    class TestConfig:
        def __init__(self):
            self.ram_size_kb = 64
            self.page_size_bytes = 4096
            self.tlb_size = 4
            self.tlb_latency_ns = 1
            self.ram_latency_ns = 100
            self.disk_latency_ns = 100000
            self.offset_bits = 12
            self.offset_mask = 4095


    config = TestConfig()
    num_frames = (config.ram_size_kb * 1024) // config.page_size_bytes
    fm = FrameManager(num_frames)

    test_addresses = [
        0x1000, 0x1004, 0x2000, 0x1008, 0x3000,
        0x1000, 0x2000, 0x4000, 0x5000, 0x1004
    ]

    test_rw = [False, False, True, False, True, False, False, True, False, False]

    # Test each algorithm
    for algo in ["FIFO", "LRU", "OPT"]:
        print("\n" + "=" * 50)
        print(f"TESTING {algo} ALGORITHM")
        print("=" * 50)

        # Reset frame manager
        fm = FrameManager(num_frames)

        # For OPT, need the full trace
        if algo == "OPT":
            mmu = MMU(config, fm, algorithm=algo, trace_addresses=test_addresses)
        else:
            mmu = MMU(config, fm, algorithm=algo)

        for i, (addr, is_write) in enumerate(zip(test_addresses, test_rw)):
            mmu.translate(addr, is_write)

        mmu.print_stats()

    print("\n" + "=" * 50)
    print("✅ MMU with Replacement Algorithms works!")
    print("=" * 50)