class TLB:
    def __init__(self, size):

        self.size = size
        self.map = {}
        # List to maintain insertion order
        self.order = []

        self.hits = 0
        self.misses = 0

    def lookup(self, vpn):

        if vpn in self.map:
            self.hits += 1
            return self.map[vpn], True
        else:
            self.misses += 1
            return None, False

    def insert(self, vpn, frame):

        if vpn in self.map:
            # Remove from order list
            self.order.remove(vpn)

        # If TLB is full, evict oldest
        elif len(self.map) >= self.size:
            self._evict_one()

        # Add new entry
        self.map[vpn] = frame
        self.order.append(vpn)

    def _evict_one(self):

        if self.order:
            oldest_vpn = self.order.pop(0)
            del self.map[oldest_vpn]

    def invalidate(self, vpn):

        if vpn in self.map:
            del self.map[vpn]
            self.order.remove(vpn)

    def flush(self):

        self.map.clear()
        self.order.clear()

    def get_hit_rate(self):

        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def get_stats(self):

        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.get_hit_rate()
        }

    def print_stats(self):

        print(f"TLB Stats: {self.hits} hits, {self.misses} misses")
        print(f"Hit rate: {self.get_hit_rate():.2%}")

    def print_contents(self):

        print("\n--- TLB Contents ---")
        if not self.map:
            print("(empty)")
        else:
            print(f"{'VPN'} {'Frame'}")
            print("-" * 20)
            for vpn in self.order:
                frame = self.map[vpn]
                print(f"{vpn} {frame}")
        print("--------------------")


# Test the module when run directly
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING TLB")
    print("=" * 50)

    # Create TLB with size 4
    tlb = TLB(size=4)

    print("\n--- Initial state ---")
    tlb.print_contents()

    print("\n--- Inserting entries 1-4 ---")
    for i in range(1, 5):
        tlb.insert(i, i * 10)
        print(f"Inserted VPN {i} → Frame {i * 10}")

    tlb.print_contents()

    print("\n--- Looking up entries ---")
    for i in range(1, 6):
        frame, hit = tlb.lookup(i)
        print(f"VPN {i}: {'HIT' if hit else 'MISS'} → Frame {frame}")

    print("\n--- Inserting VPN 5 (should evict oldest - VPN 1) ---")
    tlb.insert(5, 50)
    print("Inserted VPN 5 → Frame 50")
    tlb.print_contents()

    print("\n--- Invalidating VPN 3 ---")
    tlb.invalidate(3)
    print("Invalidated VPN 3")
    tlb.print_contents()

    print("\n--- Looking up after invalidation ---")
    frame, hit = tlb.lookup(3)
    print(f"VPN 3: {'HIT' if hit else 'MISS'}")

    print("\n--- Inserting VPN 6 ---")
    tlb.insert(6, 60)
    tlb.print_contents()

    print("\n--- Statistics ---")
    tlb.print_stats()

    print("\n" + "=" * 50)
    print("✅ TLB works!")
    print("=" * 50)