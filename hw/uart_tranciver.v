
module uart_tranciver #(
    parameter CLK_FREQ = 1000000,
    parameter BAUD_RATE = 9600
)(
    input clk,
    input rst_n,

    input [7:0] data,
    input d_valid,

    output reg uart_tx,
    output reg ready
);

    localparam IDLE = 1'b0, SEND = 1'b1;
    reg state;

    localparam CLK_DIV = CLK_FREQ/BAUD_RATE;

    reg [$clog2(CLK_DIV)-1:0] div_clk;
    reg sample_tick;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            div_clk <= 0;
            sample_tick <= 1'b0;
        end
        else begin
            if (div_clk == CLK_DIV-1) begin
                div_clk <= 0;
                sample_tick <= 1'b1;
            end
            else begin
                if (state != IDLE)
                    div_clk <= div_clk + 1;
                else
                    div_clk <= 0;

                sample_tick <= 1'b0;
            end
        end
    end

    reg [3:0] bit_count;
    reg [8:0] packet;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            ready <= 1'b0;
            uart_tx <= 1'b1;
            bit_count <= 0;
            packet <= 0;
        end
        else begin

            case(state)
                IDLE: begin
                    if (d_valid) begin
                        ready <= 1'b0;
                        state <= SEND;
                        packet <= {1'b1, data};
                        uart_tx <= 1'b0;
                        bit_count <= 0;
                    end
                    else begin
                        ready <= 1'b1;
                        uart_tx <= 1'b1;
                    end
                end
                SEND: begin
                    if (sample_tick) begin

                        if (bit_count == 10) begin
                            uart_tx <= 1'b1;
                            state <= IDLE;
                        end
                        else begin
                            uart_tx <= packet[bit_count];
                        end
                        bit_count <= bit_count + 1;
                    end
                end
            endcase
        end
    end


endmodule
