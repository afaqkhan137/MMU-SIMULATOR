class MemoryAccess:
    def __init__(self, line_num, address, is_write, original_line):
        self.line_num = line_num
        self.address = address
        self.is_write = is_write  # True = write, False = read
        self.original_line = original_line

    def __repr__(self):
        op = "WRITE" if self.is_write else "READ"
        return f"{op} {hex(self.address)} (line {self.line_num})"


def parse_trace(filename, max_address=0xFFFFFFFF):
    accesses = []
    errors = []
    line_count = 0
    read_count = 0
    write_count = 0

    try:
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line_count += 1
                original_line = line
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                parts = line.split()

                if len(parts) != 2:
                    errors.append(f"Line {line_num}: Invalid format")
                    continue

                operation, address_str = parts
                operation = operation.upper()

                # Operation valid check
                if operation not in ['R', 'W']:
                    errors.append(f"Line {line_num}: Invalid operation '{operation}' - expected R or W")
                    continue

                # Write check
                is_write = (operation in ['W'])

                address_str = address_str.strip()
                if address_str.startswith('0x') or address_str.startswith('0X'):
                    address_str = address_str[2:]

                # Convert hex to integer
                try:
                    address = int(address_str, 16)
                except ValueError:
                    errors.append(f"Line {line_num}: Invalid hex - '{address_str}'")
                    continue

                # Range check
                if address > max_address:
                    errors.append(f"Line {line_num}: Out of bounds - {hex(address)} > {hex(max_address)}")
                    continue

                # Valid access
                if is_write:
                    write_count += 1
                else:
                    read_count += 1

                accesses.append(MemoryAccess(line_num, address, is_write, original_line))

    except FileNotFoundError:
        print(f"Error: Trace file '{filename}' not found!")
        raise

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"TRACE FILE PARSING SUMMARY")
    print(f"{'=' * 50}")
    print(f"File:           {filename}")
    print(f"Total lines:    {line_count}")
    print(f"Valid accesses: {len(accesses)}")
    print(f"  Reads:        {read_count}")
    print(f"  Writes:       {write_count}")
    print(f"Errors:         {len(errors)}")

    if errors and len(errors) <= 10:
        for err in errors:
            print(f"  {err}")
    elif errors:
        print(f"  (Showing first 5 of {len(errors)} errors)")
        for err in errors[:5]:
            print(f"  {err}")

    print(f"{'=' * 50}\n")

    return accesses


def get_stats(accesses):
    if not accesses:
        return {'total': 0, 'reads': 0, 'writes': 0, 'write_percent': 0}

    reads = sum(1 for a in accesses if not a.is_write)
    writes = sum(1 for a in accesses if a.is_write)

    return {
        'total': len(accesses),
        'reads': reads,
        'writes': writes,
        'write_percent': (writes / len(accesses)) * 100
    }


# Test the module when run directly
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING TRACE PARSER")
    print("=" * 50)

    # Test with our small trace file
    accesses = parse_trace("trace_small.txt")

    # Print first 5 accesses
    print("\nFIRST 5 ACCESSES:")
    print("-" * 40)
    for acc in accesses[:5]:
        op = "WRITE" if acc.is_write else "READ"
        print(f"Line {acc.line_num}: {op} {hex(acc.address)}")

    # Print statistics
    stats = get_stats(accesses)
    print(f"\nSTATISTICS:")
    print("-" * 40)
    print(f"Total accesses: {stats['total']}")
    print(f"Reads:          {stats['reads']}")
    print(f"Writes:         {stats['writes']}")
    print(f"Write %:        {stats['write_percent']:.1f}%")

    print("\n" + "=" * 50)
    print("✅ Trace Parser works!")
    print("=" * 50)