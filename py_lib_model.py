import ctypes, struct, sys

lib = ctypes.CDLL('./libxtea.so')  # For Linux/macOS, or 'xtea.dll' for Windows

# Define the function prototype (types of parameters)

lib.encipher.argtypes = [ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
lib.encipher.restype = None

lib.decipher.argtypes = [ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
lib.decipher.restype = None

# Convert the key and data to ctypes
key = [0x11234567, 0x89ABCDEF, 0xFEDCBA98, 0x76543211]
data = [0xc1d9c4bd, 0xee67b636]

key_ctypes = (ctypes.c_uint32 * 4)(*key)
data_ctypes = (ctypes.c_uint32 * 2)(*data)
encrypted = (ctypes.c_uint32 * 2)()

print(f"Key : 0x{key[0]:x} 0x{key[1]:x} 0x{key[2]:x} 0x{key[3]:x}")
print(f"Data: 0x{data[0]:x} 0x{data[1]:x}")

# Encrypt the data
lib.encipher(data_ctypes, encrypted, key_ctypes)
print("Encrypted Data:", [hex(encrypted[0]), hex(encrypted[1])])

# Decrypt the data
decrypted = (ctypes.c_uint32 * 2)()
lib.decipher(encrypted, decrypted, key_ctypes)
print("Decrypted Data:", [hex(decrypted[0]), hex(decrypted[1])])
print(f"Sizeof Encrypted (single) {(sys.getsizeof(encrypted[0]))}")
print(f"Sizeof Encrypted (full) {(sys.getsizeof(encrypted))}")
