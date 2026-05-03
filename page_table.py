class PageTableEntry:
    def __init__(self, frame=-1, valid=0, dirty=0):

        self.frame = frame
        self.valid = valid
        self.dirty = dirty

    def __repr__(self):
        return f"PTE(frame={self.frame}, valid={self.valid}, dirty={self.dirty})"


class PageTable:

    def __init__(self):

        self.table = {}  # VPN -> PageTableEntry

    def add_entry(self, vpn, frame):

        self.table[vpn] = PageTableEntry(frame=frame, valid=1, dirty=0)

    def get_entry(self, vpn):
        return self.table.get(vpn)

    def is_valid(self, vpn):
        entry = self.table.get(vpn)
        return entry is not None and entry.valid == 1

    def get_frame(self, vpn):

        entry = self.table.get(vpn)
        if entry and entry.valid:
            return entry.frame
        return -1

    def mark_dirty(self, vpn):

        entry = self.table.get(vpn)
        if entry:
            entry.dirty = 1

    def is_dirty(self, vpn):

        entry = self.table.get(vpn)
        return entry is not None and entry.dirty == 1

    def invalidate(self, vpn):

        entry = self.table.get(vpn)
        if entry:
            entry.valid = 0
            entry.frame = -1

    def set_frame(self, vpn, frame):
        entry = self.table.get(vpn)
        if entry:
            entry.frame = frame
            entry.valid = 1
            entry.dirty = 0
        else:
            self.add_entry(vpn, frame)

    def contains(self, vpn):

        return vpn in self.table

    def print_table(self):

        print("\nPage Table Contents")
        valid_entries = [(vpn, pte) for vpn, pte in self.table.items() if pte.valid == 1]
        if not valid_entries:
            print("(empty)")
        else:
            print(f"{'VPN'} {'Frame'} {'Dirty'}")
            for vpn, pte in sorted(valid_entries):
                print(f"{vpn} {pte.frame} {pte.dirty}")


# Test the module when run directly
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING PAGE TABLE")
    print("=" * 50)

    # Create page table
    pt = PageTable()

    print("\n--- Adding entries ---")
    pt.add_entry(1, 5)  # VPN 1 → Frame 5
    pt.add_entry(2, 2)  # VPN 2 → Frame 2
    print("Added VPN 1 → Frame 5")
    print("Added VPN 2 → Frame 2")

    print("\n--- Looking up entries ---")
    print(f"VPN 1: {pt.get_entry(1)}")
    print(f"VPN 2: {pt.get_entry(2)}")
    print(f"VPN 3: {pt.get_entry(3)} (should be None)")

    print("\n--- Checking validity ---")
    print(f"Is VPN 1 valid? {pt.is_valid(1)}")
    print(f"Is VPN 3 valid? {pt.is_valid(3)}")

    print("\n--- Getting frames ---")
    print(f"Frame for VPN 1: {pt.get_frame(1)}")
    print(f"Frame for VPN 2: {pt.get_frame(2)}")

    print("\n--- Marking dirty ---")
    pt.mark_dirty(1)
    print(f"Is VPN 1 dirty? {pt.is_dirty(1)}")
    print(f"Is VPN 2 dirty? {pt.is_dirty(2)}")

    print("\n--- Invalidating VPN 1 ---")
    pt.invalidate(1)
    print(f"Is VPN 1 valid? {pt.is_valid(1)}")
    print(f"Frame for VPN 1: {pt.get_frame(1)}")
    print(f"Is VPN 1 dirty? {pt.is_dirty(1)} (dirty bit preserved!)")

    print("\n--- Setting frame for existing invalid entry ---")
    pt.set_frame(1, 10)
    print(f"Is VPN 1 valid? {pt.is_valid(1)}")
    print(f"Frame for VPN 1: {pt.get_frame(1)}")

    print("\n--- Printing full table ---")
    pt.print_table()

    print("\n" + "=" * 50)
    print("✅ Page Table works!")
    print("=" * 50)