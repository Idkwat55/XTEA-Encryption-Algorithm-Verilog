#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

void encipher(uint32_t *const v, uint32_t *const w, const uint32_t *const k) {
  register uint32_t y = v[0], z = v[1], delta = 0x9E3779B9;
  register uint32_t n = 32, sum = 0;

  while (n-- > 0) {
    printf("enc: k index is (sum&3) : %d\n", sum & 3);
    // y += (z << 4 ^ z >> 5) + z ^ sum + k[sum & 3];
    y = y + ((((z << 4) ^ (z >> 5)) + z) ^ (sum + k[sum & 3]));
    sum += delta;
    printf("enc: k index is (sum>>11&3) : %d\n", sum >> 11 & 3);
    // z += (y << 4 ^ y >> 5) + y ^ sum + k[sum >> 11 & 3];
    z = z + ((((y << 4) ^ (y >> 5)) + y) ^ (sum + k[(sum >> 11) & 3]));
  }
  w[0] = y;
  w[1] = z;
}

void decipher(uint32_t *const v, uint32_t *const w, const uint32_t *const k) {
  register uint32_t y = v[0], z = v[1], delta = 0x9E3779B9;
  register uint32_t sum = 0xc6ef3720, n = 32;
  while (n-- > 0) {

    printf("denc: k index is (sum>>11&3) : %d\n", sum >> 11 & 3);
    // z -= (y << 4 ^ y >> 5) + y ^ sum + k[sum >> 11 & 3];
    z = z - ((((y << 4) ^ (y >> 5)) + y) ^ (sum + k[(sum >> 11) & 3]));
    sum -= delta;
    printf("denc: k index is (sum&3) : %d\n", sum & 3);
    // y -= (z << 4 ^ z >> 5) + z ^ sum + k[sum & 3];
    y = y - ((((z << 4) ^ (z >> 5)) + z) ^ (sum + k[sum & 3]));
  }
  w[0] = y;
  w[1] = z;
}

int main() {
  uint32_t key[4] = {0x11234567, 0x89ABCDEF, 0xFEDCBA98, 0x76543211};
  uint32_t data[2] = {0xc1d9c4bd, 0xee67b636};
  uint32_t encrypted[2], decrypted[2];

  printf("Original Data: 0x%" PRIx32 " 0x%" PRIx32 "\n", data[0], data[1]);

  printf("Key: 0x%" PRIx32 " 0x%" PRIx32 " 0x%" PRIx32 " 0x%" PRIx32 "\n",
         key[0], key[1], key[2], key[3]);

  encipher(data, encrypted, key);
  printf("	Encrypted Data: 0x%" PRIx32 " 0x%" PRIx32 "\n", encrypted[0],
         encrypted[1]);
  uint64_t encrypted_full = ((uint64_t)encrypted[0] << 32) | encrypted[1];
  printf("	Encrypted full: 0x%" PRIx64 "\n", encrypted_full);

  decipher(encrypted, decrypted, key);

  printf("Original Data: 0x%" PRIx32 " 0x%" PRIx32 "\n", data[0], data[1]);

  printf("Key: 0x%" PRIx32 " 0x%" PRIx32 " 0x%" PRIx32 " 0x%" PRIx32 "\n",
         key[0], key[1], key[2], key[3]);
  printf("Decrypted Data: 0x%" PRIx32 " 0x%" PRIx32 "\n", decrypted[0],
         decrypted[1]);
  printf("	Encrypted Data: 0x%" PRIx32 " 0x%" PRIx32 "\n", encrypted[0],
         encrypted[1]);

  uint64_t decrypted_full = ((uint64_t)decrypted[0] << 32 | decrypted[1]);
  printf("	Encrypted full: 0x%" PRIx64 "\n", encrypted_full);
  printf("Decrypted full : 0x%" PRIx64 "\n", decrypted_full);
  printf("DONE");
  return 0;
}
