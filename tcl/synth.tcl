file mkdir results

set clk_period 10.0
set part "xc7a100tcsg324-1"

set size [list 8 16 32 64 128]
set sma_variants [list "sma_direct" "sma_recursive"]  

#SMA Synthesis
foreach var $sma_variants {
    read_verilog -sv "hw/${var}.sv"
    foreach s $size {
        synth_design -top $var -part $part -mode out_of_context -generic "N=${s}"
        create_clock -period $clk_period [get_ports clk]
        report_utilization -file "results/${var}_N${s}_utilization.rpt"
        report_timing_summary -file "results/${var}_N${s}_timing.rpt"
        close_design
    }
}

read_verilog -sv "hw/rc_filter.sv"
synth_design -top rc_filter -part $part -mode out_of_context -generic "S=4" -generic "FRAC_BITS=8"
create_clock -period $clk_period [get_ports clk]
report_utilization -file "results/rc_filter_utilization.rpt"
report_timing_summary -file "results/rc_filter_timing.rpt"
close_design

exit