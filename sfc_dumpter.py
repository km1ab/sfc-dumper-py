import sys
import RPi.GPIO as GPIO
import time

INTV = 0.005
# CLK	#RESET
port_tbl_addr_ctrl = [17, 27]

port_tbl_data_ctrl = [20, 21, 22, 23, 4, 5, 6, 7]
# CPU R/W	# /ROMSEL	# M2	# PPU /RD
port_tbl_port_ctrl = [9, 10, 11, 19]

args = sys.argv


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


# 	print(ret)
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
        # print(chr(GpioGetData()), end='')
        time.sleep(INTV)
        # GpioGetData()
        output.append(GpioGetData())
        IncAddress()
    print("")
    return output


# def ReadLoRom(addr,chrsize)
# 	ClearAddr()
# 	gpio_sleep(50)
# 	SetAddress(addr)
# 	upper = 0
# 	for i=1,chrsize*2 do
# 	    if (i-1)>upper * 2 * 0x8000 then
# 		    if 0==((i-1) % 0x8000) then
# 				upper = upper + 1
# 		    end
# 	    end
# 		address = upper * 2 * 0x8000 + ((i-1) % 0x8000) + 0x8000
# 	    if (i-1)+0x8000==address then
# 			val = gpio_get_value(port_tbl_data_ctrl[1], 0, 0xff)
# 			dumper_write(val)
# 		end
# 		IncAddress()
# 		i=i+1
# 	end
# end
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


ROM_INFO_SIZE = 25
# OE  - CpuRw
# CS  - RomSel
# WE  - M2_PpuWr
# RST - PpuRd
def MainLoop():
    if len(args) < 2:
        print("error")
        return

    path_w = args[1]
    game_info_f = False
    if (len(args)) >= 3:
        game_info_f = True  # args[2]

    InitPort()
    startAddr = 0xFFC0  # ROM Info Addr
    RomInfoSize = ROM_INFO_SIZE
    # ROM Info 25 byte
    # size = RomInfoSize + 1024
    # size = 1024 * 1024 * (24>>3)
    # size = 1

    # Read Rom Info
    # OE + CS + !WE + !RST
    DisableCpuRw()
    DisableRomSel()
    EnableM2_PpuWr()
    EnablePpuRd()
    # out = ReadRom(startAddr, RomInfoSize)
    out: list = ReadRom(startAddr, RomInfoSize)

    print("-------------------------")
    print("Game Info (Title, etc...)")
    print("-------------------------")
    # print(out)
    # for data in out:
    #     print(f" {format(data, 'x')}", end="")
    # print("")
    val_dict = {}
    size = 0
    isLoRom = False
    for i in range(4):
        val = out.pop()
        # print(f"type val={type(val)}")
        val_dict[str(ROM_INFO_SIZE - i - 1)] = int(val)
        print(f"{ROM_INFO_SIZE-i-1}: {hex(val)}")
    if val_dict["23"] == 0x0A:
        print("size: 1MB")
        size = 0x100000  # 1MB
    elif val_dict["23"] == 0x0C:
        print("size: 4MB")
        size = 0x400000  # 4MB
    else:
        print("size: unknown")
        size = 0

    if (val_dict["21"] & 0x01) == 0:
        print("LoROM")
        isLoRom = True
    else:
        print("HiROM")

    for data in out:
        print(chr(data), end="")
    print("\n-------------------------")

    if game_info_f:
        ClearAddr()
        TermPort()
        return

    ClearAddr()
    print("")
    print("OK Bokujo")

    start_address: int = 0x0000
    if isLoRom:
        start_address = conver_address(start_address)

    print(f"start_address = {hex(start_address)}")
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
        f.write(bin)

    ClearAddr()
    TermPort()
    print("")
    print("Complete!")


MainLoop()
