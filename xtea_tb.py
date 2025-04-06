# clib ctypes 
import ctypes
import struct


# path, os 
from pathlib import Path
import os
import traceback
import binascii
import random  as rnd
from colorama import Fore, Back, Style, init 
import shutil
import warnings 

# cocotb
import cocotb
from cocotb.clock import Clock 
from cocotb.triggers import RisingEdge, Timer, Event, ClockCycles, ReadOnly
from cocotb.runner import get_runner
from cocotb.log import logging, SimLog


# cocotb bus 
from cocotb_bus.drivers import BusDriver
from cocotb_bus.monitors import BusMonitor 
from cocotb_bus.scoreboard import Scoreboard

# global variables and inits
init(autoreset=True)
terminal_width = shutil.get_terminal_size().columns
warnings.filterwarnings('ignore',category=DeprecationWarning)


class IpDriver(BusDriver):
    _signals=["clk", "rst_i", "valid_i", "en_i", "data_i", "key", "decrypt_i", "result_e", "valid_o", "busy_o"]
    def __init__(self, entity, name, clk, signal, log):
        """
        entity - dut
        name - instance name
        clk - dut clk
        signal - signal to _drive 
        log - log handle
        """
        BusDriver.__init__(self=self,entity=entity, name=name,clock=clk)
        self.entity = entity 
        self.name = name 
        self.clk = clk
        self.log = log
        self.signal = signal
        
        # init & set defaults
        self.input_key = 0x1123456789ABCDEFFEDCBA9876543211

    async def _driver_send(self, transaction, sync=True):
        await RisingEdge(self.clk)
        self.entity.valid_i.value = 1 
        self.entity.en_i.value = 1 
        self.signal.value = transaction
        self.entity.key.value = self.input_key 
        await RisingEdge(self.clk)
        self.entity.valid_i.value = 0 
        self.entity.en_i.value = 0 


class SigMonitor(BusMonitor):
    def __init__(self, entity, name, clock, signal, log, callback=None, event=None):
        BusMonitor.__init__(self=self, entity=entity, name=name, clock=clock, callback=callback , event=event)
        self.signal = signal
        self.clk = clock
        self.log = log
        self.name = name
        self.entity = entity


    async def _monitor_recv(self):
        clkedge = RisingEdge(self.clock)

        while True:
            await clkedge
            vec = self.signal.value
            self._recv(vec)


class TB:
    def __init__(self, entity, name, clk, log):
        self.name=name
        self.clk = clk
        self.log = log
        self.entity = entity

        self.ip_data_list = []
        self.ip_encd_list = []
        self.op_decd_list = []
        self.key_list     = []

        self.Driver_Event = Event()
        self.drv_data_i = IpDriver(self.entity, "data_i driver", self.clk, self.entity.data_i,self.log)
        self.Monitor_Event = Event()
        self.mon_result_o = SigMonitor(entity=self.entity, name="result_o monitor", clock=self.clk, signal=self.entity.result_o, log=self.log, callback=None, event=self.Monitor_Event)

        self.sb = Scoreboard(entity)

    def print_callback(self, transaction):
        self.log.debug(f"callback (hex):  {hex(transaction)} ")


    async def reset_entity(self):
        self.entity.en_i.value=0 
        self.entity.valid_i.value=1 
        self.entity.data_i.value=0 
        self.entity.key.value=0 
        self.entity.decrypt_i.value=0
        self.entity.rst_i.value=0 
        await ClockCycles(self.clk, 2)
        self.entity.rst_i.value=1 
        await ClockCycles(self.clk, 4)
        self.entity.rst_i.value=0 
        await RisingEdge(self.clk)


    def model(self, key_cipher: int, data_cipher: int):
        try:                                        
            self.log.debug(f"[model] key_cipher    : {hex(key_cipher)}")
            self.log.debug(f"[model] data_cipher   : {hex(data_cipher)}")

            import ctypes
            import traceback

            lib = ctypes.CDLL('../libxtea.so')  

            # Define the function prototype (types of parameters)
            lib.encipher.argtypes = [
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32)
            ]
            lib.encipher.restype = None

            lib.decipher.argtypes = [
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32)
            ]
            lib.decipher.restype = None

            # Convert 128-bit key integer into four 32-bit words (little-endian)
            key = [(key_cipher >> (32 * i)) & 0xFFFFFFFF for i in reversed(range(4))]
            key_ctypes = (ctypes.c_uint32 * 4)(*key)

            # Convert 64-bit data integer into two 32-bit words (little-endian)
            data = [(data_cipher >> (32 * i)) & 0xFFFFFFFF for i in reversed(range(2))]
            data_ctypes = (ctypes.c_uint32 * 2)(*data)

            encrypted = (ctypes.c_uint32 * 2)()

            # Encrypt the data
            lib.encipher(data_ctypes, encrypted, key_ctypes)
            encrypted_result = (encrypted[0] << 32) | encrypted[1]
            self.log.debug(f"[model] Encrypted Data: {[hex(encrypted[0]), hex(encrypted[1])]} (Combined: {hex(encrypted_result)})")

            # Decrypt the data
            decrypted = (ctypes.c_uint32 * 2)()
            lib.decipher(encrypted, decrypted, key_ctypes)
            decrypted_result = (decrypted[0] << 32) | decrypted[1]
            self.log.debug(f"[model] Decrypted Data: {[hex(decrypted[0]), hex(decrypted[1])]} (Combined: {hex(decrypted_result)})")

        except Exception:
            self.log.critical("Python Model Failed")
            self.log.error(f"{traceback.format_exc()}")
            cocotb.scheduler._terminate = 1

        
@cocotb.test()
async def random_functional_test(dut):
    
    # set clock, init log, init tb class
    cocotb.start_soon(Clock(dut.clk, 2, "ns").start())
    log = SimLog("[xtea] random_functional")
    logging.getLogger().setLevel(logging.DEBUG)
    log.info("Starting Testbench for XTEA")
    tb_h = TB(dut, "TB_inst", dut.clk, log)

    data_driver = tb_h.drv_data_i 

    # reset dut 
    await tb_h.reset_entity()

    # generate random key (128-bits)
    data_driver.input_key=rnd.randint(0,340282366920938463463374607431768211456)
    log.warning(f"Generated Key: 0x{data_driver.input_key:x}")

    log.debug("")
    # send a random set of data to dut for encryption 
    for i in range(0, rnd.randint(1,32)):
        # 
        # max input is: 2 ** 64 = 18446744073709551616
        #
        temp_data = rnd.randint(0,18446744073709551616)
        tb_h.ip_data_list.append(temp_data)
        log.debug(f"[encryption]       raw data to dut on port data_i  : 0x{temp_data:x}")
        data_driver.input_data = temp_data
        await data_driver._driver_send(data_driver.input_data)
        await data_driver._wait_for_signal(dut.valid_o)

        # Read DUT output
        await ReadOnly()
        dut_val = dut.result_o.value.integer
        tb_h.ip_encd_list.append(dut_val)
        log.debug(f"[encryption] [dut] processed value on port result_o: 0x{dut_val:x}")
   

    # print total data sent, and its encrypted form 
    log.debug("")
    log.debug("[info] [raw    input   list] (hex):")
    for i in range(0, len(tb_h.ip_data_list)):
        log.debug(f"{hex(tb_h.ip_data_list[i])}")
    log.debug("") 
    log.debug("[info] [encrypted data list] (hex):")
    for i in range(0, len(tb_h.ip_data_list)):
        log.info(f"{hex(tb_h.ip_encd_list[i])}")

    # set mode to decryption
    await RisingEdge(dut.clk)
    dut.decrypt_i.value=1  
    await RisingEdge(dut.clk)

    log.debug("")
    # send encrypted data for decryption
    for i in range(0, len(tb_h.ip_encd_list)):
        log.debug(f"[decryption]       encrypted data to dut on port data_i: 0x{tb_h.ip_encd_list[i]:x}")
        await data_driver._driver_send(tb_h.ip_encd_list[i])
        await data_driver._wait_for_signal(dut.valid_o)

        # Read DUT output
        await ReadOnly()
        log.debug(f"[decryption] [dut] processed value on port result_o    : {hex(dut.result_o.value)}")
        tb_h.op_decd_list.append(dut.result_o.value.integer)

    log.debug("")
    # run model for generated random data (input list given to dut)
    for i in range(0, len(tb_h.ip_data_list)):
        tb_h.model(key_cipher=data_driver.input_key, data_cipher=tb_h.ip_data_list[i])
    
    log.debug("")
    log.debug("[info] [decrypted data list] (hex):")
    for i in range(0, len(tb_h.ip_data_list)):
        log.info(f"{hex(tb_h.op_decd_list[i])}")

    log.debug("")
    tb_h.sb.compare(tb_h.op_decd_list, tb_h.ip_data_list, log)


@cocotb.test()
async def directed_functional_test(dut):
    
    # set clock, init log, init tb class
    cocotb.start_soon(Clock(dut.clk, 2, "ns").start())
    log = SimLog("[xtea] directed_functional")
    logging.getLogger().setLevel(logging.DEBUG)
    log.info("Starting Testbench for XTEA")
    tb_h = TB(dut, "TB_inst", dut.clk, log)
   
    data_driver = tb_h.drv_data_i 

    # reset dut 
    await tb_h.reset_entity()

    # generate random key (128-bits)
    data_driver.input_key=rnd.randint(0,340282366920938463463374607431768211456)
    log.warning(f"Generated Key: 0x{data_driver.input_key:x}")
    
    # 64-bit common corner cases
    corner_cases = [
        0x0000000000000000,  # All zeros
        0xFFFFFFFFFFFFFFFF,  # All ones
        0x0000000000000001,  # Single bit set at the lowest position
        0x00000000000000FF,  # Lowest 8 bits set
        0x0000000000000FFF,  # Lowest 12 bits set
        0x000000000000FFFF,  # Lowest 16 bits set
        0x000000000000FFFFF,  # Lowest 20 bits set
        0x000000000000000F,  # Lowest 4 bits set
        0x0000000000000F0F,  # Alternating bits 1010 pattern
        0x0000000000001234,  # Random value for variety
        0x7F00000000000000,  # Sign bit set with the rest as zeros
        0x8000000000000000,  # Only the sign bit set
        0x0101010101010101,  # Alternating 1 byte pattern (01010101)
        0x5555555555555555,  # Alternating 0101 pattern
        0xAAAAAAAAAAAAAAAA,  # Alternating 1010 pattern
        0x0000000000001F1F,  # Lower 16 bits alternating 1 and 0
        0x1F1F1F1F1F1F1F1F,  # Lower 4 bits alternating
        0xFFFF000000000000,  # High 16 bits set, others zero
        0xFF00000000000000,  # First byte set to all ones
        0x0000000000FF0000,  # Middle 8 bits set
        0x00000000000000FF,  # Low byte set
        0x8000000000000001,  # Sign bit and lowest bit set
        0x01FF01FF01FF01FF,  # Alternating set bytes in 16-bit blocks
        0x003F003F003F003F,  # Pattern set in groups of 4 bits
        0x000F000F000F000F,  # Pattern set in groups of 4 bits
        0xFFFF00000000000F,  # High 16 bits set, with one low bit set
        0xFFFFFF0000000000,  # Top 24 bits set
        0x0000000000010101,  # Small walking ones (slightly staggered)
        0x0101010101010101,  # Simple walking ones (in each byte)
        0xFEFEFEFEFEFEFEFE   # Pattern in 1111 1110 pattern
    ]

    log.debug("")
    # send a random set of data to dut for encryption 
    for i in corner_cases:
        temp_data = i
        tb_h.ip_data_list.append(temp_data)
        log.debug(f"[encryption]       raw data to dut on port data_i  : 0x{temp_data:x}")
        data_driver.input_data = temp_data
        await data_driver._driver_send(data_driver.input_data)
        await data_driver._wait_for_signal(dut.valid_o)
        
        # Read DUT output
        await ReadOnly()
        dut_val = dut.result_o.value.integer
        tb_h.ip_encd_list.append(dut_val)
        log.debug(f"[encryption] [dut] processed value on port result_o: 0x{dut_val:x}")
   

    # print total data sent, and its encrypted form 
    log.debug("")
    log.debug("[info] [raw    input   list] (hex):")
    for i in range(0, len(tb_h.ip_data_list)):
        log.debug(f"{hex(tb_h.ip_data_list[i])}")
    log.debug("") 
    log.debug("[info] [encrypted data list] (hex):")
    for i in range(0, len(tb_h.ip_data_list)):
        log.info(f"{hex(tb_h.ip_encd_list[i])}")

    # set mode to decryption
    await RisingEdge(dut.clk)
    dut.decrypt_i.value=1  
    await RisingEdge(dut.clk)

    log.debug("")
    # send encrypted data for decryption
    for i in range(0, len(tb_h.ip_encd_list)):
        log.debug(f"[decryption]       encrypted data to dut on port data_i: 0x{tb_h.ip_encd_list[i]:x}")
        await data_driver._driver_send(tb_h.ip_encd_list[i])
        await data_driver._wait_for_signal(dut.valid_o)

        # Read DUT output
        await ReadOnly()
        log.debug(f"[decryption] [dut] processed value on port result_o    : {hex(dut.result_o.value)}")
        tb_h.op_decd_list.append(dut.result_o.value.integer)

    log.debug("")
    # run model for generated random data (input list given to dut)
    for i in range(0, len(tb_h.ip_data_list)):
        tb_h.model(key_cipher=data_driver.input_key, data_cipher=tb_h.ip_data_list[i])
    
    log.debug("")
    log.debug("[info] [decrypted data list] (hex):")
    for i in range(0, len(tb_h.ip_data_list)):
        log.info(f"{hex(tb_h.op_decd_list[i])}")

    log.debug("")
    tb_h.sb.compare(tb_h.op_decd_list, tb_h.ip_data_list, log)

@cocotb.test()
async def directed_key_test(dut):
    
    # set clock, init log, init tb class
    cocotb.start_soon(Clock(dut.clk, 2, "ns").start())
    log = SimLog("[xtea] directed_key")
    logging.getLogger().setLevel(logging.DEBUG)
    log.info("Starting Testbench for XTEA")
    tb_h = TB(dut, "TB_inst", dut.clk, log)
   
    data_driver = tb_h.drv_data_i 

    # reset dut 
    await tb_h.reset_entity()

    # generate random data (64-bits)
    tb_h.ip_data_list.append(rnd.randint(0,18446744073709551616))
    log.warning(f"Generated Data: 0x{tb_h.ip_data_list[0]:x}")

    tb_h.key_list = [
        0x00000000000000000000000000000000,  # All 0s
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # All 1s
        0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # Alternating 1010
        0x55555555555555555555555555555555,  # Alternating 0101
        0x80000000000000000000000000000000,  # Only MSB set
        0x00000000000000000000000000000001,  # Only LSB set
        0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # All but MSB set
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # All but LSB set
        0xF0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0,  # Alternating nibbles F0
        0x0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F,  # Alternating nibbles 0F
        0xABCDABCDABCDABCDABCDABCDABCDABCD,  # Repeating 16-bit block
        0x12345678123456781234567812345678,  # Repeating 32-bit block
        0x0000000000000000FFFFFFFFFFFFFFFF,  # Half 0s, half 1s
        0xFFFFFFFFFFFFFFFF0000000000000000,  # Half 1s, half 0s
        0x000102030405060708090A0B0C0D0E0F,  # Incrementing bytes
        0x0F0E0D0C0B0A09080706050403020100,  # Decrementing bytes
        0xF0F0F0F0F0F0F0F00F0F0F0F0F0F0F0F,  # Half F0s, half 0Fs
        0xDEADBEEFDEADBEEFDEADBEEFDEADBEEF,  # Pattern: DEADBEEF
        0xCAFEBABECAFEBABECAFEBABECAFEBABE,  # Pattern: CAFEBABE
        0x0F0F0F0F0F0F0F0FF0F0F0F0F0F0F0F0,  # Bit mirrored halves
        0x5E2A9B48D0C1F34B7E0D6A3C9B7F0EAD,  # High entropy random
        0x11111111111111111111111111111111,  # All bytes = 0x11
        0xEFEFEFEFEFEFEFEFEFEFEFEFEFEFEFEF,  # All bytes = 0xEF
        0x01010101010101010101010101010101,  # 1-bit spaced pattern
        0xFEFEFEFEFEFEFEFEFEFEFEFEFEFEFEFE,  # Inverse of above
        0xFFFFFFFF00000000FFFFFFFF00000000,  # Patterned halves
        0x00000000FFFFFFFF00000000FFFFFFFF,  # Shifted version
        0x13579BDF2468ACE013579BDF2468ACE0,  # Odd/Even pattern
        0x89ABCDEF0123456789ABCDEF01234567,  # Split high/low nibbles
        0xFFEEDDCCBBAA99887766554433221100   # Descending hex Pattern 
    ]

    log.debug("")
    # send a random key to dut for encryption 
    for i in range(0, len(tb_h.key_list)):
        temp_data = tb_h.key_list[i]
        data_driver.input_key = temp_data
        log.debug(f"[encryption]       raw key to dut on port key      : 0x{data_driver.input_key:x}")
        data_driver.input_data = tb_h.ip_data_list[0]
        await data_driver._driver_send(data_driver.input_data)
        await data_driver._wait_for_signal(dut.valid_o)
        

        # Read DUT output
        await ReadOnly()
        dut_val = dut.result_o.value.integer
        tb_h.ip_encd_list.append(dut_val)
        log.debug(f"[encryption] [dut] processed value on port result_o: 0x{dut_val:x}")
   

    # print total data sent, and its encrypted form 
    log.debug("")
    log.debug("[info] [raw    input   list] (hex):")
    for i in range(0, len(tb_h.ip_data_list)):
        log.debug(f"{hex(tb_h.ip_data_list[i])}")
    log.debug("") 
    log.debug("[info] [encrypted data list] (hex):")
    for i in range(0, len(tb_h.key_list)):
        log.info(f"{hex(tb_h.ip_encd_list[i])}")

    # set mode to decryption
    await RisingEdge(dut.clk)
    dut.decrypt_i.value=1  
    await RisingEdge(dut.clk)

    log.debug("")
    # send encrypted data for decryption
    for i in range(0, len(tb_h.ip_encd_list)):
        data_driver.input_key=tb_h.key_list[i]
        log.debug(f"[decryption]       encrypted data to dut on port data_i: 0x{tb_h.ip_encd_list[i]:x}")
        await data_driver._driver_send(tb_h.ip_encd_list[i])
        await data_driver._wait_for_signal(dut.valid_o)

        # Read DUT output
        await ReadOnly()
        log.debug(f"[decryption] [dut] processed value on port result_o    : {hex(dut.result_o.value)}")
        tb_h.op_decd_list.append(dut.result_o.value.integer)

    log.debug("")
    # run model for generated random data (input list given to dut)
    for i in range(0, len(tb_h.key_list)):
        tb_h.model(key_cipher=tb_h.key_list[i], data_cipher=tb_h.ip_data_list[0])
    
    log.debug("")
    log.debug("[info] [decrypted data list] (hex):")
    for i in range(0, len(tb_h.ip_data_list)):
        log.info(f"{hex(tb_h.op_decd_list[i])}")

    log.debug("")
    for i in range(len(tb_h.key_list)-1):
        tb_h.ip_data_list.append(tb_h.ip_data_list[0])
    tb_h.sb.compare(tb_h.op_decd_list, tb_h.ip_data_list, log)

def print_col(message: str, mode: int, pad:int):
    """
    Print colored message with different styles based on mode.
    pad - 0 : No padding
    pad 1 : add padding
    0 - BLACK on WHITE
    1 - WHITE on YELLOW
    2 - WHITE on GREEN
    """
  
    if pad==1 and len(message) < terminal_width:
        padded = (terminal_width - len(message)) // 2
        message = " " * padded + message + " " * padded

   
    if mode == 0:
        print(Fore.BLACK + Back.WHITE + message)
    elif mode == 1:
        print(Fore.WHITE + Back.YELLOW + Style.DIM + message)
    elif mode == 2:
        print(Fore.WHITE + Back.GREEN + message)
    else:
        print("Invalid mode. Choose 0, 1, or 2.")


def start_build():
    print_col("[MAIN] Starting TB",0,1)
    sim = os.getenv("SIM","verilator")
    proj_dir = Path(__file__).resolve().parent
    verilog_sources = [proj_dir/"xtea.v"]
    hdl_toplevel = "xtea"
    test_module = "xtea_tb"
    

    if (sim=="verilator"):
        build_args = ["--trace","--trace-fst"]
        print_col("[MAIN] Simulator: Verilator",0,1)
        print_col("[MAIN] FST Path : ./sim_build/dump.fst",0,1)
    else:
        build_args=[]
    

    log_file=None 
    log_en = os.getenv("EN_LOG",None)
    if(log_en != None):
        log_file = f"./sim_build/{test_module}.log"
        print_col("[MAIN] Test Log Path: ./sim_build/"+ test_module +".log",0,1)
        try: 
            f = open(log_file, "w+")
            f.close()
        except Exception:
            print_col("[ERROR] Log file can't be opened or created",0,1)
            print(Exception)
    else:
        print_col("[MAIN] set EN_LOG to 1 for log file generation",1,1)


    runner = get_runner(sim)
    runner.build(
            hdl_toplevel = hdl_toplevel,
            build_args = build_args,
            verilog_sources = verilog_sources,
            always = True,
            waves = True
    )

    runner.test(
        hdl_toplevel = hdl_toplevel,
        test_module= test_module,
        waves = True,
        log_file=log_file
    )

    print_summary()


if __name__ == "__main__":
    start_build()
