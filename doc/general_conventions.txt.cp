
Data representation and storage:

	for a given key (128 bits) "11234567 89abcdef fedcba98 76543211"
	data is stored as follows:
		first byte '11234567' is stored at k[0]

	Then,
		Data	11234567  89abcdef  fedcba98  76543211
		Byte 	k[0]      k[1]      k[2]      k[3]
		Bit	[127:96]  [ 95:64]  [ 63:32]  [ 31:0]
	

	for a given data (64 bits) "12345678 9abcdef1"
	data is stored as follows:
		first byte '12345678' is stored at v[0] (also y)

	Then,
		Data	12345678  9abcdef
		Byte	v[0]      v[1]
		Bit 	[ 63:32]  [ 31:0]
