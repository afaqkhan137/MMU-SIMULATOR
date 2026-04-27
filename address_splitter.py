
def split_address(virtual_address, offset_bits, offset_mask):

    vpn = virtual_address >> offset_bits
    offset = virtual_address & offset_mask

    return vpn, offset

def print_address_breakdown(address, vpn, offset, page_size_bytes):

    print(f"\nAddress: {hex(address)} ({address})")
    print(f" Page Size: {page_size_bytes} bytes")
    print(f" VPN: {vpn} ")
    print(f" Offset: {offset}")

# TEST CODE
if __name__ == "__main__":
    print("=" * 50)
    print("TESTING ADDRESS SPLITTER")
    print("=" * 50)

    # Test configuration
    TEST_PAGE_SIZE = 4096
    TEST_OFFSET_BITS = 12
    TEST_OFFSET_MASK = TEST_PAGE_SIZE - 1  # 4095

    # Test addresses from our trace file
    test_addresses = [
        0x00001000,  # 4096
        0x00001004,  # 4100
        0x00002000,  # 8192
        0x00001008,  # 4104
        0x00003000,  # 12288
    ]

    print(f"\nPage Size: {TEST_PAGE_SIZE} bytes")
    print(f"Offset Bits: {TEST_OFFSET_BITS}")
    print(f"Offset Mask: 0x{TEST_OFFSET_MASK:X}\n")

    print("-" * 50)
    print(f"{'Address':<12} {'Hex':<12} {'VPN':<8} {'Offset':<8}")
    print("-" * 50)

    for addr in test_addresses:
        vpn, offset = split_address(addr, TEST_OFFSET_BITS, TEST_OFFSET_MASK)
        print(f"{addr:<12} {hex(addr):<12} {vpn:<8} {offset:<8}")

    print("-" * 50)

    # Detailed breakdown for first address
    print_address_breakdown(test_addresses[0], 1, 0, TEST_PAGE_SIZE)

    print("\n" + "=" * 50)
    print("✅ Address Splitter works!")
    print("=" * 50)