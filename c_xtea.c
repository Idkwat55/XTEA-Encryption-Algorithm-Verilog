#include <stdint.h>
#include <stdio.h>

void encipher(uint32_t *const v, uint32_t *const w, const uint32_t *const k) {
  register uint32_t y = v[0], z = v[1], delta = 0x9E3779B9;
  register uint32_t n = 32, sum = 0;

  // printf("Initial : sum %d (%x) y %d (%x) z %d (%x)\n", sum, sum, y, y, z,
  // z);
  while (n-- > 0) {
    y += (z << 4 ^ z >> 5) + z ^ sum + k[sum & 3];
    sum += delta;
    z += (y << 4 ^ y >> 5) + y ^ sum + k[sum >> 11 & 3];
    // printf("round[%2d] sum %32d y %32d z %32d\n", limit, sum, y, z);
  }
  w[0] = y;
  w[1] = z;
  // printf("Final : y %d (%x) z %d (%x)\n", y, y, z, z);
}

void decipher(uint32_t *const v, uint32_t *const w, const uint32_t *const k) {
  register uint32_t y = v[0], z = v[1], delta = 0x9E3779B9;
  register uint32_t sum = 0xc6ef3720, n = 32;
  /* sum = delta<<5, in general sum = delta * n */
  while (n-- > 0) {
    z -= (y << 4 ^ y >> 5) + y ^ sum + k[sum >> 11 & 3];
    sum -= delta;
    y -= (z << 4 ^ z >> 5) + z ^ sum + k[sum & 3];
  }
  w[0] = y;
  w[1] = z;
}

/*
int main() {
  uint32_t key[4] = {0x01234567, 0x89ABCDEF, 0xFEDCBA98, 0x76543210};
  uint32_t data[2] = {0x12345678, 0x9ABCDEF0};
  uint32_t encrypted[2], decrypted[2];

  printf("Original Data: %lx %lx\n", data[0], data[1]);

  printf("Key: %lx %lx %lx %lx\n", key[0], key[1], key[2], key[3]);

  encipher(data, encrypted, key);
  printf("Encrypted Data: %lx %lx\n", encrypted[0], encrypted[1]);

  decipher(encrypted, decrypted, key);
  printf("Decrypted Data: %lx %lx\n", decrypted[0], decrypted[1]);

  return 0;
}
*/
