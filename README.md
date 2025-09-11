# XTEA Algorithm:
Verilog FSM based implementation of XTEA Algorithm. A Dual core version is also included.
Complete with Cocotb based Testbench.

# DUT behaviour 
DUT takes in 64bit data, and 128bit key and based on the decrypt signal it either encrypts or decrypts the data. 
Internally it uses 32 Feistel rounds. The DUT follows original XTEA descriptions.
Single core version is `xtea.v`, dual core version can be found in `xtea_cores.v`

# Testbench 
Ensure you have cocotb and cocotb_bus libraries installed and run the `xtea_tb.py` like any normal python script - for single core test, or `xtea_cores_tb.py` for dual core test.
For single core test, total of ~92 test cases are defined, including random and directed data and key.

By default, logging level is set to `DEBUG`, you can change this to `INFO` by setting the `COCOTB_LOG_LEVEL` env variable, or manually setting log level by manipulating the `getLogger().setLevel()`

By default, testbench result are directed to stdout, you can set `EN_LOG` env variable to capture logs into a logfile.

By default, FST waveform named `dump.fst` should be produced in the `sim_build` directory.

A similar testbench in verilog is also provided, `xtea_tb_v.v`.

# Docs
Refer `docs` folder for more information.
