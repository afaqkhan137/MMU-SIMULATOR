class FIFO:
    def __init__(self):
        self.queue = []

    def record_access(self, vpn):
        if vpn not in self.queue:
            self.queue.append(vpn)

    def evict(self):
        if not self.queue:
            return None  # Return None instead of raising Exception
        return self.queue.pop(0)

    def invalidate(self, vpn):
        if vpn in self.queue:
            self.queue.remove(vpn)


class LRU:
    def __init__(self):
        self.order = []

    def record_access(self, vpn):
        if vpn in self.order:
            self.order.remove(vpn)
        self.order.append(vpn)

    def evict(self):
        if not self.order:
            return None
        return self.order.pop(0)

    def invalidate(self, vpn):
        if vpn in self.order:
            self.order.remove(vpn)

class OPT:

    def __init__(self, trace_addresses, offset_bits):
        # Convert all addresses to VPNs
        self.vpn_sequence = [addr >> offset_bits for addr in trace_addresses]

        # Future use list
        self.next_use = {}

        # Pre-scan all trace addresses
        from collections import defaultdict
        positions = defaultdict(list)

        for idx, vpn in enumerate(self.vpn_sequence):
            positions[vpn].append(idx)

        # For each position, find next occurrence
        for vpn, pos_list in positions.items():
            for i, pos in enumerate(pos_list):
                next_pos = pos_list[i + 1] if i + 1 < len(pos_list) else float('inf')
                self.next_use[(vpn, pos)] = next_pos

    def evict(self, current_index, vpns_in_ram):
        farthest_vpn = None
        farthest_distance = -1

        for vpn in vpns_in_ram:
            next_use = self.next_use.get((vpn, current_index), float('inf'))
            if next_use > farthest_distance:
                farthest_distance = next_use
                farthest_vpn = vpn

        if farthest_vpn is None:
            raise Exception("No pages to evict!")
        return farthest_vpn


# Test the module when run directly
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING REPLACEMENT ALGORITHMS")
    print("=" * 50)

    # Test FIFO
    print("\n--- Testing FIFO ---")
    fifo = FIFO()
    for vpn in [1, 2, 3, 1, 4, 5]:
        fifo.record_access(vpn)
    print(f"Queue order: {fifo.queue}")
    print(f"Evict: {fifo.evict()} (should be 1)")
    print(f"Queue after evict: {fifo.queue}")

    # Test LRU
    print("\n--- Testing LRU ---")
    lru = LRU()
    for vpn in [1, 2, 3, 1, 4, 5]:
        lru.record_access(vpn)
    print(f"LRU order (most recent at end): {lru.order}")
    print(f"Evict: {lru.evict()} (should be 2)")
    print(f"Order after evict: {lru.order}")

    # Test OPT
    print("\n--- Testing OPT ---")
    trace_addrs = [0x1000, 0x2000, 0x1000, 0x3000, 0x4000, 0x2000]
    offset_bits = 12
    opt = OPT(trace_addrs, offset_bits)
    vpns_in_ram = [1, 2, 3]  # VPN 1,2,3
    print(f"VPNs in RAM: {vpns_in_ram}")
    print(f"At position 2, evict: {opt.evict(2, vpns_in_ram)}")

    print("\n" + "=" * 50)
    print("✅ Replacement Algorithms work!")
    print("=" * 50)