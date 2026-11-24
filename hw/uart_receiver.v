
module uart_receiver #(
    parameter int CLK_FREQ = 10000000,
    parameter int BAUD_RATE = 9600,
    parameter int OVERSAMPLING = 16
)(
    input clk,
    input rst_n,

    input uart_rx,

    output reg d_valid,
    output reg [7:0] odata,
    output reg error
);

    localparam int CLK_DIV = CLK_FREQ/(BAUD_RATE*OVERSAMPLING);

    reg [($clog2(CLK_DIV)-1):0] div_clk;
    reg sample_clk;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_clk <= 1'b0;
            div_clk <= 0;
        end
        else begin
            if (div_clk == CLK_DIV - 1) begin
                sample_clk <= 1'b1;
                div_clk <= 0;
            end
            else begin
                div_clk <= div_clk + 1;
                sample_clk <= 1'b0;
            end
        end
    end

    localparam [1:0] IDLE = 2'b00, START = 2'b01, DATA = 2'b10, EVAL = 2'b11;

    reg [1:0] state;
    reg [9:0] rdata_buff;

    reg [3:0] bit_count;
    reg [($clog2(OVERSAMPLING)-1):0] sample_count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            rdata_buff <= 1'b0;
            sample_count <= 0;
            bit_count <= 0;
            error <= 1'b0;
            d_valid <= 1'b0;
        end
        else begin
            error <= 1'b0;
            d_valid <= 1'b0;

            case(state)
                IDLE: begin
                    bit_count <= 0;
                    sample_count <= 0;

                    if (!uart_rx) begin
                        state <= START;
                    end
                end
                START: begin
                    if (sample_clk) begin
                        if (sample_count == (OVERSAMPLING/2) - 1) begin
                            sample_count <= 0;
                            if (!uart_rx)
                                state <= DATA;
                            else
                                state <= IDLE;
                        end
                        else begin
                            sample_count <= sample_count + 1;
                        end
                    end
                end
                DATA: begin
                    if (sample_clk) begin
                        if (sample_count == OVERSAMPLING - 1) begin
                            sample_count <= 0;
                            if (bit_count == 10) begin
                                state <= EVAL;
                            end
                            else begin
                                rdata_buff <= {uart_rx, rdata_buff[9:1]};
                                bit_count <= bit_count + 1;
                            end
                        end
                        else begin
                            sample_count <= sample_count + 1;
                        end
                    end
                end
                EVAL: begin
                    if ((^rdata_buff[8:0]) || (!rdata_buff[9])) begin
                        error <= 1'b1;
                    end
                    else begin
                        d_valid <= 1'b1;
                        odata <= rdata_buff[7:0];
                    end
                    state <= IDLE;
                end
            endcase

        end
    end

endmodule
