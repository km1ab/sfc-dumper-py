import sys
import RPi.GPIO as GPIO
import time
from options import get_option

INTV = 0.005
# CLK	#RESET
port_tbl_addr_ctrl = [17, 27]

port_tbl_data_ctrl = [20, 21, 22, 23, 4, 5, 6, 7]
# CPU R/W	# /ROMSEL	# M2	# PPU /RD
port_tbl_port_ctrl = [9, 10, 11, 19]

ROM_INFO_ADDR = 0xFFC0
# ROM Info 32 byte
ROM_INFO_SIZE = 32


class Debug:
    def __init__(self, fdebug: bool):
        self.f_debug_log: bool = fdebug

    def dbg_print(self, log_msg, kaigyo: bool = True):
        if self.f_debug_log:
            if kaigyo:
                print(log_msg)
            else:
                print(log_msg, end="")


def InitPort():
    GPIO.setmode(GPIO.BCM)
    for d in port_tbl_addr_ctrl:
        GPIO.setup(d, GPIO.OUT)
    for d in port_tbl_data_ctrl:
        GPIO.setup(d, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    for d in port_tbl_port_ctrl:
        GPIO.setup(d, GPIO.OUT)


def TermPort():
    GPIO.cleanup()


def GpioOut(d, f):
    GPIO.output(d, f)


def GpioIn(d):
    return GPIO.input(d)


def GpioGetData():
    ret = (
        ((GpioIn(port_tbl_data_ctrl[0]) << 0))
        | ((GpioIn(port_tbl_data_ctrl[1]) << 1))
        | ((GpioIn(port_tbl_data_ctrl[2]) << 2))
        | ((GpioIn(port_tbl_data_ctrl[3]) << 3))
        | ((GpioIn(port_tbl_data_ctrl[4]) << 4))
        | ((GpioIn(port_tbl_data_ctrl[5]) << 5))
        | ((GpioIn(port_tbl_data_ctrl[6]) << 6))
        | ((GpioIn(port_tbl_data_ctrl[7]) << 7))
    )
    return ret


# 	dbg.dbg_print(ret)
# 	return ord(hex(ret))


def ClearAddr():
    GpioOut(port_tbl_addr_ctrl[1], True)
    GpioOut(port_tbl_addr_ctrl[1], False)


def SetAddress(addr):
    GpioOut(port_tbl_addr_ctrl[0], True)
    GpioOut(port_tbl_addr_ctrl[1], True)
    time.sleep(INTV)
    GpioOut(port_tbl_addr_ctrl[1], False)
    for i in range(addr):
        GpioOut(port_tbl_addr_ctrl[0], False)
        GpioOut(port_tbl_addr_ctrl[0], True)


def IncAddress():
    GpioOut(port_tbl_addr_ctrl[0], False)
    GpioOut(port_tbl_addr_ctrl[0], True)


def SetPortCtrl(i):
    GpioOut(port_tbl_port_ctrl[i], True)


def ClearPortCtrl(i):
    GpioOut(port_tbl_port_ctrl[i], False)


def EnableCpuRw():
    SetPortCtrl(0)


def DisableCpuRw():
    ClearPortCtrl(0)


def EnableRomSel():
    SetPortCtrl(1)


def DisableRomSel():
    ClearPortCtrl(1)


def EnableM2_PpuWr():
    SetPortCtrl(2)


def DisableM2_PpuWr():
    ClearPortCtrl(2)


def EnablePpuRd():
    SetPortCtrl(3)


def DisablePpuRd():
    ClearPortCtrl(3)


def ReadRom(addr, chrsize) -> list:
    ClearAddr()
    time.sleep(INTV)
    SetAddress(addr)
    time.sleep(INTV)
    output = []
    for i in range(chrsize):
        # dbg.dbg_print(chr(GpioGetData()), end='')
        time.sleep(INTV)
        # GpioGetData()
        output.append(GpioGetData())
        IncAddress()
    print("")
    return output


def conver_address(in_addr: int) -> int:
    address = in_addr
    upper = int(address / 0x8000)
    lower = address % 0x8000
    address = upper * 2 * 0x8000 + lower + 0x8000
    if (address % 0x8000) == 0:
        # clear addr
        ClearAddr()
        # set addr
        SetAddress(address)

    return address


def get_d_info(header_info: dict):
    val_dict = {}
    out = header_info.copy()
    for i in range(11):
        val = out.pop()
        val_dict[str(ROM_INFO_SIZE - i - 1)] = int(val)
    title = "".join([chr(_) for _ in out])
    return val_dict, title


def print_binary_view(dbg: Debug, startaddr: int, data: dict):
    dbg.dbg_print("======================================================")
    addr = startaddr
    dbg.dbg_print("     |", False)
    for value in range(16):
        formated = format(value, "02x").upper()
        dbg.dbg_print(f" {formated}", False)
    dbg.dbg_print("\n------------------------------------------------------", False)
    idx = 0
    for value in data:
        if idx % 16 == 0:
            dbg.dbg_print("")
            formated = format(addr + idx, "04x").upper()
            dbg.dbg_print(f"{formated} |", False)
        formated = format(value, "02x").upper()
        dbg.dbg_print(f" {formated}", False)
        idx = idx + 1
    dbg.dbg_print("")
    dbg.dbg_print("======================================================")


# FFD5h
#   Bit 0-3 マッピングモード
#           0x0: LoROM/32K Banks             Mode 20 (LoROM)
#           0x1: HiROM/64K Banks             Mode 21 (HiROM)
#           0x2: LoROM/32K Banks + S-DD1     Mode 22 (mappable) "Super MMC"
#           0x3: LoROM/32K Banks + SA-1      Mode 23 (mappable) "Emulates Super MMC"
#           0x5: HiROM/64K Banks             Mode 25 (ExHiROM)
#           0xA: HiROM/64K Banks + SPC7110   Mode 25? (mappable)
#   Bit 4   動作速度
#           0: Slow(200ns)
#           1: Fast(120ns)
#   Bit 5   0b1(bit4とbit5の2bitでROMの動作クロック(2 or 3)を表していると思われる)
#   Bit 6-7 0b00
def print_game_info(dbg: Debug, header_info: list, size: int, isLoRom: bool):

    val_dict, title = get_d_info(header_info)

    print("-------------------------")
    print("Game Info (Title, etc...)")
    print("-------------------------")
    print(f"Title:    {title}")

    romsize_s = "unknown"
    if (size >> 10) != 0:
        romsize = 0 if size == 0 else size >> 20
        romsize_s = f"{romsize}MB" if romsize != 0 else f"{size >> 10 }KB"
    print(f"Size:     {romsize_s}")

    romtype = "LoROM" if isLoRom else "HiROM"
    dbg.dbg_print(f"Type:     {romtype}")

    dbg.dbg_print(f"Header Data:")
    print_binary_view(dbg, ROM_INFO_ADDR, header_info)

    dbg.dbg_print("Detail: ")
    for key, value in sorted(val_dict.items()):
        formated = format(value, "#04x")
        dbg.dbg_print(f"  {hex(int(key))}: {formated}")

    print("\n-------------------------")
    ClearAddr()
    TermPort()
    dbg.dbg_print("")
    dbg.dbg_print("OK Bokujo \(^o^)/")


def calc_check_sum(bin):
    sum = 0
    for value in bin:
        sum = sum + value
    print("\nCheck Sum: ", end="")
    print(format(sum % 0x10000, "04x").upper())


# OE  - CpuRw
# CS  - RomSel
# WE  - M2_PpuWr
# RST - PpuRd
def MainLoop():
    opt = get_option()
    path_w = opt["filename"]
    game_info_f = opt["gameinfo"]
    f_debug_log = opt["debug"]
    dbg = Debug(f_debug_log)

    InitPort()
    startAddr = ROM_INFO_ADDR  # ROM Info Addr
    RomInfoSize = ROM_INFO_SIZE

    # Read Rom Info
    # OE + CS + !WE + !RST
    DisableCpuRw()
    DisableRomSel()
    EnableM2_PpuWr()
    EnablePpuRd()
    header_info: list = ReadRom(startAddr, RomInfoSize)

    size = 0
    isLoRom = False

    if header_info[0x17] > 0x00:
        size = 1 << (header_info[0x17] + 10)

    if (header_info[0x15] & 0x01) == 0:
        isLoRom = True

    if game_info_f:
        print_game_info(dbg, header_info, size, isLoRom)
        return

    ClearAddr()

    start_address: int = 0x0000
    if isLoRom:
        start_address = conver_address(start_address)

    dbg.dbg_print(f"start_address = {hex(start_address)}")
    SetAddress(start_address)
    time.sleep(INTV)
    bin = bytearray([])
    n_mod = 1
    if size > 8:
        n_mod = size >> 3
    with open(path_w, mode="wb") as f:
        for i in range(size):
            if i % n_mod == 0:
                sys.stdout.write("#")
                sys.stdout.flush()
                time.sleep(0.001)

            if isLoRom:
                conver_address(i)

            bin.append(GpioGetData())
            IncAddress()
        calc_check_sum(bin)
        f.write(bin)

    ClearAddr()
    TermPort()
    print("")
    print("Complete!")


try:
    MainLoop()
except Exception as ex:
    ClearAddr()
    TermPort()
    print(f"error: {ex}")
