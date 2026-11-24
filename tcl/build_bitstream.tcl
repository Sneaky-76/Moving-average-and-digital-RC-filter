# Build full bitstream for Nexys 4 DDR
file mkdir hw/build

set part "xc7a100tcsg324-1"

puts "=== Reading design sources ==="
read_verilog -sv hw/top.sv
read_verilog -sv hw/sma_direct.sv
read_verilog -sv hw/sma_recursive.sv
read_verilog -sv hw/rc_filter.sv
read_verilog -sv hw/uart_receiver.v
read_verilog -sv hw/uart_tranciver.v
read_xdc hw/nexys4ddr.xdc

puts "=== Synthesizing top design ==="
synth_design -top top -part $part

puts "=== Optimizing logic ==="
opt_design

puts "=== Placement ==="
place_design

puts "=== Routing ==="
route_design

puts "=== Generating reports ==="
report_utilization -file hw/build/top_utilization.rpt
report_timing_summary -file hw/build/top_timing.rpt

puts "=== Writing bitstream ==="
write_bitstream -force hw/build/nexys4ddr_filter.bit

puts "=========================================================="
puts "=== Bitstream ready: hw/build/nexys4ddr_filter.bit ==="
puts "=========================================================="
exit
