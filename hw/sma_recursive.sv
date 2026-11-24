module sma_recursive #(
    parameter int N = 16,
    parameter int DATA_WIDTH = 8
) (
    input logic clk,
    input logic rst_n,
    input logic valid_in,
    input logic signed [DATA_WIDTH-1:0] data_in,
    
    output logic valid_out,
    output logic signed [DATA_WIDTH-1:0] data_out
);

    localparam int DIV = $clog2(N);
    localparam int SUM_SIZE = DATA_WIDTH + DIV;

    logic signed [DATA_WIDTH-1:0] buffer [0:N-1];
    
    logic signed [SUM_SIZE-1:0] sum;
    logic signed [SUM_SIZE-1:0] prev_sum;
    logic signed [DATA_WIDTH-1:0] result;


    always_ff @( posedge clk or negedge rst_n ) begin : sma

        if (!rst_n) begin
            prev_sum <= '0;
            data_out <= '0;
            valid_out <= 1'b0;
            for (int i = 0; i < N; i++) buffer[i] <= '0;
        end else begin
            if (valid_in) begin
                prev_sum <= sum;
                valid_out <= 1'b1;
                data_out <= result;
                buffer[0] <= data_in;
                for (int i=1; i<N; i++) buffer[i] <= buffer[i-1];
            end else begin
                valid_out <= 1'b0;
            end
        end
        
    end

    always_comb begin : adder
        sum = prev_sum + data_in - buffer[N-1];
        result = sum >>> DIV;
    end

endmodule
