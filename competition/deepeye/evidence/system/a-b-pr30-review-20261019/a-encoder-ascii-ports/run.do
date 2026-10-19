onerror {quit -code 8}
onbreak {quit -code 7}
vsim -voptargs=+acc work.main_encoder_port_tb {+INPUT=C:/Users/CarlJade/Documents/CodexBuildLinks/deepeye-pr30-20261019/a-encoder-ascii-ports/cases.txt} {+OUTPUT=C:/Users/CarlJade/Documents/CodexBuildLinks/deepeye-pr30-20261019/a-encoder-ascii-ports/ports.txt}
run -all
quit -code 0
