`timescale 1ns / 1ps

module xtea_tb_v;

  reg          clk;
  reg          rst_i;
  reg          valid_i;
  reg          en_i;
  reg  [ 63:0] data_i;
  reg  [127:0] key;
  reg          decrypt_i;

  wire [ 63:0] result_o;
  wire         valid_o;
  wire         busy_o;

  // Instantiate DUT
  xtea dut (
      .clk      (clk),
      .rst_i    (rst_i),
      .valid_i  (valid_i),
      .en_i     (en_i),
      .data_i   (data_i),
      .key      (key),
      .decrypt_i(decrypt_i),
      .result_o (result_o),
      .valid_o  (valid_o),
      .busy_o   (busy_o)
  );

  // Clock generation
  initial clk = 0;
  always #1 clk = ~clk;  // 2ns period

  // Simple reset
  task reset_dut;
    begin
      rst_i = 0;
      valid_i = 0;
      en_i = 0;
      data_i = 64'd0;
      key = 128'd0;
      decrypt_i = 0;
      repeat (4) @(posedge clk);
      rst_i = 1;
      repeat (4) @(posedge clk);
      rst_i = 0;
      @(posedge clk);
    end
  endtask

  // Drive a single transaction
  task send_data(input [63:0] din, input [127:0] k, input dec);
    begin
      @(posedge clk);
      data_i    <= din;
      key       <= k;
      decrypt_i <= dec;
      valid_i   <= 1;
      en_i      <= 1;
      @(posedge clk);
      valid_i <= 0;
      en_i    <= 0;
      @(posedge clk);
    end
  endtask

  // ----------------------------
  // Randomized test
  // ----------------------------
  task random_test;
    integer i;
    reg [63:0] data_mem[0:7];
    reg [63:0] enc_mem[0:7];
    reg [127:0] rand_key;
    begin
      reset_dut;
      rand_key  = 128'h1123456789ABCDEFFEDCBA9876543211;

      decrypt_i = 0;
      for (i = 0; i < 32; i = i + 1) begin
        data_mem[i] = $random;
        send_data(data_mem[i], rand_key, 0);
        wait (valid_o);
        @(posedge clk);
        enc_mem[i] = result_o;
        $display("[random_data_test][ enc] data_in=0x%h -> result=0x%h", data_mem[i], enc_mem[i]);
      end

      decrypt_i = 1;
      for (i = 0; i < 8; i = i + 1) begin
        send_data(enc_mem[i], rand_key, 1);
        wait (valid_o);
        @(posedge clk);
        $display("[random_data_test][dec ] enc_in=0x%h -> result=0x%h", enc_mem[i], result_o);
      end
    end
  endtask

  // ----------------------------
  // Directed data test
  // ----------------------------
  task directed_data_test;
    integer i;
    reg [63:0] data_cases[0:29];  // fill with 30 corner cases
    reg [63:0] enc_mem[0:29];
    reg [127:0] fixed_key;
    begin
      reset_dut;
      fixed_key = 128'h0123456789ABCDEF_FEDCBA9876543210;  // example key 

      // Direct Conrer cases
      data_cases[0] = 64'h0000000000000000;  // All zeros
      data_cases[1] = 64'hFFFFFFFFFFFFFFFF;  // All ones
      data_cases[2] = 64'h0000000000000001;  // Single bit set at the lowest position
      data_cases[3] = 64'h00000000000000FF;  // Lowest 8 bits set
      data_cases[4] = 64'h0000000000000FFF;  // Lowest 12 bits set
      data_cases[5] = 64'h000000000000FFFF;  // Lowest 16 bits set
      data_cases[6] = 64'h000000000000FFFF;  // Lowest 20 bits set
      data_cases[7] = 64'h000000000000000F;  // Lowest 4 bits set
      data_cases[8] = 64'h0000000000000F0F;  // Alternating bits 1010 pattern
      data_cases[9] = 64'h0000000000001234;  // Random value for variety
      data_cases[10] = 64'h7F00000000000000;  // Sign bit set with the rest as zeros
      data_cases[11] = 64'h8000000000000000;  // Only the sign bit set
      data_cases[12] = 64'h0101010101010101;  // Alternating 1 byte pattern (01010101)
      data_cases[13] = 64'h5555555555555555;  // Alternating 0101 pattern
      data_cases[14] = 64'hAAAAAAAAAAAAAAAA;  // Alternating 1010 pattern
      data_cases[15] = 64'h0000000000001F1F;  // Lower 16 bits alternating 1 and 0
      data_cases[16] = 64'h1F1F1F1F1F1F1F1F;  // Lower 4 bits alternating
      data_cases[17] = 64'hFFFF000000000000;  // High 16 bits set, others zero
      data_cases[18] = 64'hFF00000000000000;  // First byte set to all ones
      data_cases[19] = 64'h0000000000FF0000;  // Middle 8 bits set
      data_cases[20] = 64'h00000000000000FF;  // Low byte set
      data_cases[21] = 64'h8000000000000001;  // Sign bit and lowest bit set
      data_cases[22] = 64'h01FF01FF01FF01FF;  // Alternating set bytes in 16-bit blocks
      data_cases[23] = 64'h003F003F003F003F;  // Pattern set in groups of 4 bits
      data_cases[24] = 64'h000F000F000F000F;  // Pattern set in groups of 4 bits
      data_cases[25] = 64'hFFFF00000000000F;  // High 16 bits set, with one low bit set
      data_cases[26] = 64'hFFFFFF0000000000;  // Top 24 bits set
      data_cases[27] = 64'h0000000000010101;  // Small walking ones (slightly staggered)
      data_cases[28] = 64'h0101010101010101;  // Simple walking ones (in each byte)
      data_cases[29] = 64'hFEFEFEFEFEFEFEFE;  // Pattern in 1111 1110 pattern


      decrypt_i = 0;
      for (i = 0; i < 30; i = i + 1) begin
        send_data(data_cases[i], fixed_key, 0);
        wait (valid_o);
        @(posedge clk);
        enc_mem[i] = result_o;
        $display("[directed_data_test][ enc] data_case[%0d]=0x%h -> result=0x%h", i, data_cases[i],
                 enc_mem[i]);
      end

      decrypt_i = 1;
      for (i = 0; i < 30; i = i + 1) begin
        send_data(enc_mem[i], fixed_key, 1);
        wait (valid_o);
        @(posedge clk);
        $display("[directed_data_test][dec ] enc_case[%0d]=0x%h -> result=0x%h", i, enc_mem[i],
                 result_o);
      end
    end
  endtask

  // ----------------------------
  // Directed key test
  // ----------------------------
  task directed_key_test;
    integer i;
    reg [127:0] key_cases[0:29];  // fill with 30 corner-case keys
    reg [63:0] enc_mem[0:29];
    reg [63:0] fixed_data;
    begin
      reset_dut;
      fixed_data = 64'hDEADBEEFCAFEBABE;  // example input data

      // TODO: you populate key_cases[...] with your 30 values


      key_cases[0] = 128'h00000000000000000000000000000000;  // All 0s
      key_cases[1] = 128'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;  // All 1s
      key_cases[2] = 128'hAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;  // Alternating 1010
      key_cases[3] = 128'h55555555555555555555555555555555;  // Alternating 0101
      key_cases[4] = 128'h80000000000000000000000000000000;  // Only MSB set
      key_cases[5] = 128'h00000000000000000000000000000001;  // Only LSB set
      key_cases[6] = 128'h7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;  // All but MSB set
      key_cases[7] = 128'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE;  // All but LSB set
      key_cases[8] = 128'hF0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0;  // Alternating nibbles F0
      key_cases[9] = 128'h0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F;  // Alternating nibbles 0F
      key_cases[10] = 128'hABCDABCDABCDABCDABCDABCDABCDABCD;  // Repeating 16-bit block
      key_cases[11] = 128'h12345678123456781234567812345678;  // Repeating 32-bit block
      key_cases[12] = 128'h0000000000000000FFFFFFFFFFFFFFFF;  // Half 0s, half 1s
      key_cases[13] = 128'hFFFFFFFFFFFFFFFF0000000000000000;  // Half 1s, half 0s
      key_cases[14] = 128'h000102030405060708090A0B0C0D0E0F;  // Incrementing bytes
      key_cases[15] = 128'h0F0E0D0C0B0A09080706050403020100;  // Decrementing bytes
      key_cases[16] = 128'hF0F0F0F0F0F0F0F00F0F0F0F0F0F0F0F;  // Half F0s, half 0Fs
      key_cases[17] = 128'hDEADBEEFDEADBEEFDEADBEEFDEADBEEF;  // Pattern: DEADBEEF
      key_cases[18] = 128'hCAFEBABECAFEBABECAFEBABECAFEBABE;  // Pattern: CAFEBABE
      key_cases[19] = 128'h0F0F0F0F0F0F0F0FF0F0F0F0F0F0F0F0;  // Bit mirrored halves
      key_cases[20] = 128'h5E2A9B48D0C1F34B7E0D6A3C9B7F0EAD;  // High entropy random
      key_cases[21] = 128'h11111111111111111111111111111111;  // All bytes = 0x11
      key_cases[22] = 128'hEFEFEFEFEFEFEFEFEFEFEFEFEFEFEFEF;  // All bytes = 0xEF
      key_cases[23] = 128'h01010101010101010101010101010101;  // 1-bit spaced pattern
      key_cases[24] = 128'hFEFEFEFEFEFEFEFEFEFEFEFEFEFEFEFE;  // Inverse of above
      key_cases[25] = 128'hFFFFFFFF00000000FFFFFFFF00000000;  // Patterned halves
      key_cases[26] = 128'h00000000FFFFFFFF00000000FFFFFFFF;  // Shifted version
      key_cases[27] = 128'h13579BDF2468ACE013579BDF2468ACE0;  // Odd/Even pattern
      key_cases[28] = 128'h89ABCDEF0123456789ABCDEF01234567;  // Split high/low nibbles
      key_cases[29] = 128'hFFEEDDCCBBAA99887766554433221100;  // Descending hex Pattern 



      decrypt_i = 0;
      for (i = 0; i < 30; i = i + 1) begin
        send_data(fixed_data, key_cases[i], 0);
        wait (valid_o);
        @(posedge clk);
        enc_mem[i] = result_o;
        $display("[directed_key_test][ enc] key_case[%0d]=0x%h -> result=0x%h", i, key_cases[i],
                 enc_mem[i]);
      end

      decrypt_i = 1;
      for (i = 0; i < 30; i = i + 1) begin
        send_data(enc_mem[i], key_cases[i], 1);
        wait (valid_o);
        @(posedge clk);
        $display("[directed_key_test][dec ] enc_key[%0d]=0x%h -> result=0x%h", i, enc_mem[i],
                 result_o);
      end
    end
  endtask

  // ----------------------------
  // Test sequence
  // ----------------------------
  initial begin

    $dumpvars;
    $dumpfile("xtea_tb_v.fst");

    $display("Starting xtea_tb_v tests:");
    $display("Running  xtea_tb_v test: random_data_test");
    random_test();
    $display("Running  xtea_tb_v test: directed_data_test");
    repeat (2) @(posedge clk);
    directed_data_test();
    $display("Running  xtea_tb_v test: directed_key_test");
    repeat (2) @(posedge clk);
    directed_key_test();
    $display("All tests Done!");
    repeat (5) @(posedge clk);
    $finish;
  end

endmodule

