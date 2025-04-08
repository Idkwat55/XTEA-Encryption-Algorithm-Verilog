/**********************************************************************************************************************/
/*                                                    XTEA Cipher                                                     */
/*                                        Multi-Core Throughput Scaled module                                         */
/*                                                                                                                    */
/*                                Github: https://github.com/Idkwat55?tab=repositories                                */
/*                                                                                                                    */
/*                                                    Risikesvar G                                                    */
/*                                                      Roshan G                                                      */
/**********************************************************************************************************************/

`default_nettype none

module xtea_cores (
    input wire clk,
    input wire rst_i,
    input wire valid_i,
    input wire en_i,
    input wire [63:0] data_a_i,
    input wire [63:0] data_b_i,
    input wire [127:0] key,
    input wire decrypt_i,
    output reg [63:0] result_a_o,
    output reg [63:0] result_b_o,
    output reg valid_o,
    output reg busy_o
);

  wire [63:0] result_a_o_w, result_b_o_w;
  wire valid_o_a_w, valid_o_b_w;
  wire busy_o_a_w, busy_o_b_w;

  // Instantiate cores
  // core 1
  xtea core_1 (
      .clk(clk),
      .rst_i(rst_i),
      .valid_i(valid_i),
      .en_i(en_i),
      .data_i(data_a_i),
      .key(key),
      .decrypt_i(decrypt_i),
      .result_o(result_a_o_w),
      .valid_o(valid_o_a_w),
      .busy_o(busy_o_a_w)
  );

  // core 2
  xtea core_2 (
      .clk(clk),
      .rst_i(rst_i),
      .valid_i(valid_i),
      .en_i(en_i),
      .data_i(data_b_i),
      .key(key),
      .decrypt_i(decrypt_i),
      .result_o(result_b_o_w),
      .valid_o(valid_o_b_w),
      .busy_o(busy_o_b_w)
  );

  // Update valid and busy
  always @(busy_o_a_w or busy_o_b_w or valid_o_a_w or valid_o_b_w) begin
    valid_o <= valid_o_a_w & valid_o_b_w;
    busy_o  <= busy_o_a_w & busy_o_b_w;
  end

  // Update result
  always @(result_a_o_w or result_b_o_w) begin
    result_a_o <= result_a_o_w;
    result_b_o <= result_b_o_w;
  end

endmodule
