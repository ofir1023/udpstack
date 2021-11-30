def calculate_checksum(data: bytes) -> int:
    if len(data) % 2 == 1:
        data += b"\0"
    s = 0
    for i in range(0, len(data), 2):
        w = data[i + 1] + (data[i] << 8)
        c = s + w
        s = (c & 0xffff) + (c >> 16)
    return ~s & 0xffff
