module rc_filter #(
    parameter int DATA_WIDTH = 8,
    parameter int FRAC_BITS = 8,
    parameter int S = 4
) (
    input logic clk,
    input logic rst_n,
    input logic valid_in,
    input logic signed [DATA_WIDTH-1:0] data_in,
    
    output logic valid_out,
    output logic signed [DATA_WIDTH-1:0] data_out
);

    localparam int WIDTH = DATA_WIDTH + FRAC_BITS;

    logic signed [WIDTH-1:0] x_scaled;
    logic signed [WIDTH:0] diff;

    logic signed [WIDTH-1:0] prev_y;
    logic signed [WIDTH-1:0] next_y;

    always_ff @( posedge clk or negedge rst_n ) begin : rc
        if (!rst_n) begin
            prev_y <= '0;
            valid_out <= '0;
            data_out <= '0;
        end else begin
            if (valid_in) begin
                valid_out <= 1'b1;
                data_out <= next_y >>> FRAC_BITS;
                prev_y <= next_y;
            end else begin
                valid_out <= 1'b0;
            end
        end
    end

    always_comb begin : adder
        x_scaled = 16'(data_in) <<< FRAC_BITS;
        diff = signed'(x_scaled) - signed'(prev_y);
        next_y = prev_y + signed'(diff >>> S);
    end

endmodule
