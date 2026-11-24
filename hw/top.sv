module top #(
    parameter int CLK_FREQ = 100_000_000,
    parameter int BAUD     = 115200
) (
    input  logic       clk,
    input  logic       rst_n,      // CPU_RESETN on Nexys 4 DDR (active low)
    input  logic [1:0] sw,         // SW[1:0] filter mode selection
    input  logic       uart_rx,    // UART RX from USB-UART bridge
    output logic       uart_tx,    // UART TX to USB-UART bridge
    output logic [3:0] led         // Status LEDs
);

    // =========================================================================
    // 1. UART Receiver
    // =========================================================================
    logic [7:0] rx_data;
    logic       rx_valid;
    logic       rx_error;

    uart_receiver #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD_RATE(BAUD)
    ) u_rx (
        .clk(clk),
        .rst_n(rst_n),
        .uart_rx(uart_rx),
        .odata(rx_data),
        .d_valid(rx_valid),
        .error(rx_error)
    );

    // =========================================================================
    // 2. Hardware Filters running in parallel
    // =========================================================================
    logic signed [7:0] sma_dir_out;
    logic              sma_dir_valid;

    sma_direct #(
        .N(16),
        .DATA_WIDTH(8)
    ) u_sma_direct (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(rx_valid),
        .data_in(signed'(rx_data)),
        .valid_out(sma_dir_valid),
        .data_out(sma_dir_out)
    );

    logic signed [7:0] sma_rec_out;
    logic              sma_rec_valid;

    sma_recursive #(
        .N(16),
        .DATA_WIDTH(8)
    ) u_sma_recursive (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(rx_valid),
        .data_in(signed'(rx_data)),
        .valid_out(sma_rec_valid),
        .data_out(sma_rec_out)
    );

    logic signed [7:0] rc_out;
    logic              rc_valid;

    rc_filter #(
        .DATA_WIDTH(8),
        .FRAC_BITS(8),
        .S(4)
    ) u_rc_filter (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(rx_valid),
        .data_in(signed'(rx_data)),
        .valid_out(rc_valid),
        .data_out(rc_out)
    );

    // =========================================================================
    // 3. Output Multiplexer based on SW[1:0]
    // =========================================================================
    logic [7:0] tx_data;
    logic       tx_valid;

    always_comb begin
        case (sw)
            2'b00: begin
                // Mode 0: Raw Bypass
                tx_data  = rx_data;
                tx_valid = rx_valid;
            end
            2'b01: begin
                // Mode 1: Variant 0 - Direct SMA (N=16)
                tx_data  = unsigned'(sma_dir_out);
                tx_valid = sma_dir_valid;
            end
            2'b10: begin
                // Mode 2: Variant 1 - Recursive SMA (N=16)
                tx_data  = unsigned'(sma_rec_out);
                tx_valid = sma_rec_valid;
            end
            2'b11: begin
                // Mode 3: Variant 2 - Digital RC Filter (S=4, Q8.8)
                tx_data  = unsigned'(rc_out);
                tx_valid = rc_valid;
            end
            default: begin
                tx_data  = rx_data;
                tx_valid = rx_valid;
            end
        endcase
    end

    // =========================================================================
    // 4. UART Transmitter
    // =========================================================================
    logic tx_ready;

    uart_tranciver #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD_RATE(BAUD)
    ) u_tx (
        .clk(clk),
        .rst_n(rst_n),
        .data(tx_data),
        .d_valid(tx_valid),
        .uart_tx(uart_tx),
        .ready(tx_ready)
    );

    // =========================================================================
    // 5. Status LEDs
    // =========================================================================
    // LED[1:0] display selected filter mode:
    // 00 = Bypass, 01 = SMA Direct, 10 = SMA Recursive, 11 = RC Filter
    assign led[0] = sw[0];
    assign led[1] = sw[1];

    // Activity indicators (pulse stretchers for visible LED blink)
    logic [20:0] rx_blink_cnt;
    logic [20:0] tx_blink_cnt;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_blink_cnt <= '0;
            tx_blink_cnt <= '0;
        end else begin
            if (rx_valid) rx_blink_cnt <= 21'd1_000_000;
            else if (rx_blink_cnt > 0) rx_blink_cnt <= rx_blink_cnt - 1;

            if (tx_valid) tx_blink_cnt <= 21'd1_000_000;
            else if (tx_blink_cnt > 0) tx_blink_cnt <= tx_blink_cnt - 1;
        end
    end

    assign led[2] = (rx_blink_cnt > 0);
    assign led[3] = (tx_blink_cnt > 0);

endmodule
