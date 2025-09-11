/**********************************************************************************************************************/
/*                                                    XTEA Cipher                                                     */
/*                                                    Main module                                                     */
/*                                                                                                                    */
/*                                Github: https://github.com/Idkwat55?tab=repositories                                */
/*                                                                                                                    */
/*                                                    Risikesvar G                                                    */
/**********************************************************************************************************************/

`default_nettype none

module xtea (
    input  wire         clk,        // Input Clock signal
    input  wire         rst_i,      // Input Reset signal
    input  wire         valid_i,    // Input Valid
    input  wire         en_i,       // Input Enable
    input  wire [ 63:0] data_i,     // Input data    :  64-bits, to be split into 32-bit words
    input  wire [127:0] key,        // Input key     : 128-bits, to be split into 32-bit words
    input  wire         decrypt_i,  // Input Mode    : 0 for Encryption / 1 for Decryption
    output reg  [ 63:0] result_o,   // Output Result : holds the encrypted / decrypted output
    output reg          valid_o,    // Output Valid
    output reg          busy_o      // Output Busy
);

  // FSM state definition
  localparam reg [2:0] IDLE = 3'b000;
  localparam reg [2:0] ENC_Y = 3'b001;
  localparam reg [2:0] ENC_S = 3'b010;
  localparam reg [2:0] ENC_Z = 3'b011;
  localparam reg [2:0] DENC_Z = 3'b100;
  localparam reg [2:0] DENC_S = 3'b101;
  localparam reg [2:0] DENC_Y = 3'b110;
  localparam reg [2:0] DONE = 3'b111;

  // register declaration
  reg [2:0] state;
  reg [31:0] k[4];
  reg [31:0] y, z, limit, sum;
  reg [31:0] delta;

  // always block defining xtea
  always @(posedge clk or posedge rst_i) begin : xtea
    if (rst_i) begin : reset_block
      state <= IDLE;
      valid_o <= 0;
      busy_o <= 0;
      result_o <= 0;
      delta <= 32'h9e3779b9;  // derived from Golden ratio
      sum <= 0;

    end else begin : xtea_core
      case (state)

        IDLE: begin
          busy_o  <= 0;
          valid_o <= 0;
          if (valid_i & en_i) begin
            k[0] <= key[127:96];  // First word
            k[1] <= key[95:64];  // Second word
            k[2] <= key[63:32];  // Third word
            k[3] <= key[31:0];  // Fourth word
            y <= data_i[63:32];  // Upper Half
            z <= data_i[31:0];  // Lower half
            busy_o <= 1;
            if (decrypt_i) begin : Encryption
              state <= DENC_Z;
              sum   <= 32'hc6ef3720;  // delta * 32
            end else begin : Decryption
              limit <= 32'hc6ef3720;  // delta * 32
              state <= ENC_Y;
              sum   <= 0;
            end
          end
        end

        ENC_Y: begin
          y <= y + ((((z << 4) ^ (z >> 5)) + z) ^ (sum + k[sum&3]));
          state <= ENC_S;
        end

        ENC_S: begin
          sum   <= sum + delta;
          state <= ENC_Z;
        end

        ENC_Z: begin
          z <= z + ((((y << 4) ^ (y >> 5)) + y) ^ (sum + k[(sum>>11)&3]));
          if (sum != limit) begin
            state <= ENC_Y;
          end else begin
            state <= DONE;
          end
        end

        DENC_Z: begin
          z <= z - ((((y << 4) ^ (y >> 5)) + y) ^ (sum + k[(sum>>11)&3]));
          state <= DENC_S;
        end

        DENC_S: begin
          sum   <= sum - delta;
          state <= DENC_Y;
        end

        DENC_Y: begin
          y <= y - ((((z << 4) ^ (z >> 5)) + z) ^ (sum + k[sum&3]));
          if (sum != 0) begin
            state <= DENC_Z;
          end else begin
            state <= DONE;
          end
        end

        DONE: begin
          valid_o <= 1;
          // assgin output = {y ,z} which corresponds to {w[0] , w[1]} with w[0] being higher order
          result_o <= {y, z};
          state <= IDLE;
        end

        default: begin
          state <= IDLE;
        end

      endcase
    end
  end

endmodule


