#!/usr/bin/env python3
# coding=utf-8

import argparse
import sys
import math
import cmd2
import mmap
import json
from cmd2 import with_category
from cmd2.table_creator import (Column, BorderedTable, HorizontalAlignment)
from colorama import Fore, Style
import time

class RunControlApp(cmd2.Cmd):

    def __init__(self):
        super().__init__(allow_cli_args=False)
        del cmd2.Cmd.do_edit
        del cmd2.Cmd.do_macro
        del cmd2.Cmd.do_run_pyscript
        del cmd2.Cmd.do_shortcuts

        self.prompt = 'RC> '
        self.prompt = cmd2.ansi.style(self.prompt, fg=cmd2.ansi.Fg.LIGHT_GREEN)

        self.columns = []
        self.columns.append(Column("31...24", width=10, header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
        self.columns.append(Column("23...16", width=10, header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
        self.columns.append(Column("15...8", width=10, header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
        self.columns.append(Column("7...0", width=10, header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
        self.bt = BorderedTable(self.columns)

        try:
            self.fid = open('/dev/uio0', 'r+b', 0)
        except FileNotFoundError:
            self.perror("UIO device not found")
            sys.exit(-1)
        self.regs = mmap.mmap(self.fid.fileno(), 0x10000)

        cmd2.categorize(
            (cmd2.Cmd.do_alias, cmd2.Cmd.do_help, cmd2.Cmd.do_history, cmd2.Cmd.do_quit, cmd2.Cmd.do_set, cmd2.Cmd.do_run_script, cmd2.Cmd.do_shell),
            "General commands"
        )

    def prsuccess(self, msg) -> None:
        self.poutput(cmd2.ansi.style(msg, fg=cmd2.ansi.Fg.LIGHT_BLUE))

    def checkRange(self, value, minVal, maxVal) -> bool:
        if value < minVal or value > maxVal:
            self.perror(f'Error: value out of range {minVal}-{maxVal} - got {value}')
            return False
        return True

    #
    # read register
    #
    def read_reg(self, add) -> int:
        return int.from_bytes(self.regs[add*4:(add*4)+4], byteorder='little')

    #
    # write register
    #
    def write_reg(self, add, value) -> None:
        self.regs[add*4:(add*4)+4] = int.to_bytes(value, 4, byteorder='little')

    #
    # read UIO register parser
    #
    read_parser = argparse.ArgumentParser()
    read_parser.add_argument('address', type=int, nargs='*', help='decimal or hexadecimal (prefix 0x)')

    @cmd2.with_argparser(read_parser)
    @cmd2.with_category("UIO commands")
    def do_read(self, args) -> None:
        """Read UIO register"""
        for channel in args.address:
            value = self.read_reg(channel)
            self.poutput(f'0x{value:08x} ({value})')

    #
    # write UIO register parser
    #
    write_parser = argparse.ArgumentParser()
    write_parser.add_argument('address', type=int, help='decimal or hexadecimal (prefix 0x)')
    write_parser.add_argument('value', help='decimal or hexadecimal (prefix 0x)')

    @cmd2.with_argparser(write_parser)
    @cmd2.with_category("UIO commands")
    def do_write(self, args) -> None:
        """Write UIO register"""
        try:
            value = int(args.value, 0)
            self.write_reg(args.address, value)
            self.poutput(f'0x{value:08x} ({value})')
        except:
            self.perror(f'Write register error')

    #
    # dump UIO register
    #
    dump_parser = argparse.ArgumentParser()
    dump_parser.add_argument('address', type=int, help='decimal or hexadecimal (prefix 0x)')

    @cmd2.with_argparser(dump_parser)
    @cmd2.with_category("UIO commands")
    def do_dump(self, args) -> None:
        """Dump UIO register"""
        value = self.regs[args.address*4:(args.address*4)+4]
        data_list = [[format(value[3], '08b'), format(value[2], '08b'), format(value[1], '08b'), format(value[0], '08b')],
                     [f'0x{value[3]:02x}', f'0x{value[2]:02x}', f'0x{value[1]:02x}', f'0x{value[0]:02x}', ]]
        table = self.bt.generate_table(data_list)
        self.poutput(table)

    #
    # print channels status
    #
    @cmd2.with_category("Monitoring commands")
    def do_status(self, _) -> None:
        """Show 19 channel status"""
        ch_en_reg = format(self.read_reg(0), '019b')
        pow_en_reg = format(self.read_reg(1), '019b')
        ratemeters = []
        for i in range(8, 27):
            ratemeters.append(self.read_reg(i))
        deadtime = self.read_reg(27)
        def ch(channel):
            on = Fore.GREEN + f"{channel+1:02}" if pow_en_reg[18-channel] == '1' else Fore.RED + f"{channel+1:02}"
            enabled = Fore.GREEN + "•" if ch_en_reg[18-channel] == '1' else Fore.RED + "•"
            return f"{on}{enabled}{Style.RESET_ALL}"

        status_scheme = [
            f"      {ch(11)}  {ch(0)}  {ch(1)}",
            f"   {ch(10)}  {ch(17)}  {ch(12)}  {ch(2)}",
            f"{ch(9)}   {ch(16)}  {ch(18)}  {ch(13)}  {ch(3)}",
            f"   {ch(8)}  {ch(15)}  {ch(14)}  {ch(4)}",
            f"      {ch(7)}  {ch(6)}  {ch(5)}",
        ]
        ratemeters_scheme = [
            f"              {ratemeters[11]:08} {ratemeters[0]:08} {ratemeters[1]:08}",
            f"         {ratemeters[10]:08} {ratemeters[17]:08} {ratemeters[12]:08} {ratemeters[2]:08}",
            f"{ratemeters[9]:08} {ratemeters[16]:08} {ratemeters[18]:08} {ratemeters[13]:08} {ratemeters[3]:08}",
            f"         {ratemeters[8]:08} {ratemeters[15]:08} {ratemeters[14]:08} {ratemeters[4]:08}",
            f"              {ratemeters[7]:08} {ratemeters[6]:08} {ratemeters[5]:08}",
        ]

        self.poutput("Number color: on/off - Dot color: enabled/disabled - Right: ratemeters")
        for status, rate in zip(status_scheme, ratemeters_scheme):
            print(status, " ", rate)
        self.poutput(f"Deadtime: {deadtime}")

    #
    # enable channel acquisition
    #
    enable_parser = argparse.ArgumentParser()
    enable_parser.add_argument('value', nargs="*", type=int, help='channel to enable on (1-19)')
    enable_parser.add_argument('-a', "--all", action="store_true", help='enable all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(enable_parser)
    def do_enable(self, args) -> None:
        """Enable channel acquisition"""
        if args.all:
            self.write_reg(0, 0X7FFFF)
            self.prsuccess("All channels enabled")
        else:
            for channel in args.value:
                if self.checkRange(channel, 1, 19):
                    self.write_reg(0, self.read_reg(0) | (1 << (channel-1)))
                    self.prsuccess(f"Channel {channel} enabled")

    #
    # disable channel acquisition
    #
    disable_parser = argparse.ArgumentParser()
    disable_parser.add_argument('value', nargs="*", type=int, help='channel to disable (1-19)')
    disable_parser.add_argument('-a', "--all", action="store_true", help='disable all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(enable_parser)
    def do_disable(self, args) -> None:
        """Disable channel acquisition"""
        if args.all:
            self.write_reg(0, 0)
            self.prsuccess("All channels disabled")
        else:
            for channel in args.value:
                if self.checkRange(channel, 1, 19):
                    self.write_reg(0, self.read_reg(0) & ~(1 << (channel-1)))
                    self.prsuccess(f"Channel {channel} disabled")

    #
    # tun on channels
    #
    on_parser = argparse.ArgumentParser()
    on_parser.add_argument('value', nargs="*", type=int, help='turn on channels (1-19)')
    on_parser.add_argument('-a', "--all", action="store_true", help='turn on all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(on_parser)
    def do_on(self, args) -> None:
        """Turn on channels"""
        if args.all:
            self.write_reg(1, 0X7FFFF)
            self.prsuccess("All channels enabled")
        else:
            for channel in args.value:
                if self.checkRange(channel, 1, 19):
                    self.write_reg(1, self.read_reg(1) | (1 << (channel-1)))
                    self.prsuccess(f"Channel {channel} enabled")

    #
    # turn off channels
    #
    off_parser = argparse.ArgumentParser()
    off_parser.add_argument('value', nargs="*", type=int, help='turn off channels (1-19)')
    off_parser.add_argument('-a', "--all", action="store_true", help='turn off all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(off_parser)
    def do_off(self, args) -> None:
        """Turn off channels"""
        if args.all:
            self.write_reg(1, 0)
            self.prsuccess("All channels disabled")
        else:
            for channel in args.value:
                if self.checkRange(channel, 1, 19):
                    self.write_reg(1, self.read_reg(1) & ~(1 << (channel-1)))
                    self.prsuccess(f"Channel {channel} disabled")

    #
    # clock register
    #
    @cmd2.with_category("Monitoring commands")
    def do_clock(self, _) -> None:
        """Check clock registers"""
        clock_reg = self.read_reg(3)
        self.poutput(f"PLL: {'locked' if (clock_reg&0x2) > 0 else 'free running'} and {'unstable' if (clock_reg&0x8000) > 0 else 'stable'}")
        self.poutput(f"Cable 1: {'OK' if (clock_reg&0x80) > 0 else 'not OK'}, {'Lost' if (clock_reg&0x40) > 0 else 'not Lost'}, {'Found' if (clock_reg&0x20) > 0 else 'not Found'}")
        self.poutput(f"Cable 2: {'OK' if (clock_reg&0x10) > 0 else 'not OK'}, {'Lost' if (clock_reg&0x8) > 0 else 'not Lost'}, {'Found' if (clock_reg&0x4) > 0 else 'not Found'}")
        self.poutput(f"Sources: {'Quartz' if (clock_reg&0x200) > 0 else 'Cable'} (set to {'Quartz' if (self.read_reg(4)&0x400) > 0 else 'Cable'})"
                     f" - cable {'2' if (clock_reg&0x100) > 0 else '1'} (set to {'2' if (self.read_reg(4)&0x800) > 0 else '1'})")

    #
    # Tr32 register
    #
    @cmd2.with_category("Monitoring commands")
    def do_tr(self, _) -> None:
        """Check Tr32 registers"""
        clock_reg = self.read_reg(3)
        self.poutput(f"Tr32: {'not received' if (clock_reg&0x800) > 0 else 'received'} and {'not aligned' if (clock_reg&0x400) > 0 else 'aligned'} - counted: {self.read_reg(45)}")
        self.poutput(f"TagT: {'not received' if (clock_reg&0x2000) > 0 else 'received'} and {'not aligned' if (clock_reg&0x1000) > 0 else 'aligned'} ({'parity not ok' if (clock_reg&0x4000) > 0 else 'parity ok'})")

    #
    # change clk source
    #
    clk_parser = argparse.ArgumentParser()
    clk_subparsers = clk_parser.add_subparsers(dest='subcommand')

    clk_source_parser = clk_subparsers.add_parser('source', help='clock souce external or internal')
    clk_source_parser.add_argument('value', type=str, help='E or I')

    clk_cable_parser = clk_subparsers.add_parser('cable', help='cable source')
    clk_cable_parser.add_argument('value', type=int, help='1 or 2')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(clk_parser)
    def do_clk_source(self, args) -> None:
        """Change clk source"""
        if args.subcommand == 'source':
            if args.value.upper() == 'E':
                self.write_reg(4, self.read_reg(4) & 0x1FBFF)
                self.prsuccess("Cable source set to external")
            elif args.value.upper() == 'I':
                self.write_reg(4, self.read_reg(4) | 0x400)
                self.prsuccess("Cable source set to internal")
            else:
                self.perror(f'Invalid value {args.value}')
        elif args.subcommand == 'cable':
            if args.value == 1:
                self.write_reg(4, self.read_reg(4) & 0x1F7FF)
                self.prsuccess("Cable source set to cable 1")
            elif args.value == 2:
                self.write_reg(4, self.read_reg(4) | 0x800)
                self.prsuccess("Cable source set to cable 2")
            else:
                self.perror(f'Invalid value {args.value}')

    #
    # enable tr32 channel
    #
    @cmd2.with_category("Slow control commands")
    def do_enable_Tr32(self, _) -> None:
        """Enable Tr32 channel"""
        state = self.read_reg(4) & 0x4000
        if state > 0:
            self.write_reg(4, self.read_reg(4) & 0x1BFFF)
            self.prsuccess("Tr32 channel disabled")
        else:
            self.write_reg(4, self.read_reg(4) | 0x4000)
            self.prsuccess("Tr32 channel enabled")

    #
    # ADC calibration
    #
    @cmd2.with_category("Slow control commands")
    def do_calibration(self, _) -> None:
        """Do a calibration measure for all the 19 ADCs"""
        answer = input("Enable calibration? (y/N) ")
        if answer.upper() == 'Y':
            self.write_reg(4, self.read_reg(4) | 0x10000)
            self.write_reg(4, self.read_reg(4) & 0xFFFF)
            self.prsuccess("Calibration performed in the next event")
        elif answer.upper() == 'N' or answer == '':
            self.perror("Calibration not performed")
        else:
            self.perror(f'Invalid response')

    #
    # pulser control
    #
    pulser_parser = argparse.ArgumentParser()
    pulser_parser.add_argument('value', nargs='*', help='pulser value (Hz), use sub to add subhits')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(pulser_parser)
    def do_pulser(self, args) -> None:
        """Control pulser"""
        if args.value[0] == 'sub':
            if len(args.value) == 1:
                self.perror("Insert number of pulses")
            elif len(args.value) == 2:
                self.write_reg(60, int(args.value[1]))
                self.prsuccess(f"Subhits added: {args.value[1]}")
            else:
                self.perror("Invalid number of pulses")
        else:
            try:
                pulsi = int(args.value[0])
                if pulsi == 0 or pulsi >= 1_000_000:
                    self.write_reg(7, pulsi)
                    self.prsuccess("Pulser OFF")
                else:
                    self.write_reg(7, int(1_000_000/int(args.value[0])))
                    self.prsuccess(f"Pulser set to {args.value[0]} Hz")
            except TypeError:
                self.perror("Invalid pulser value")

    #
    # reset multichannel / FIFO
    #
    rst_parser = argparse.ArgumentParser()
    rst_subparsers = rst_parser.add_subparsers(dest='subcommand')

    rst_multi_parser = rst_subparsers.add_parser('multi', help='toggle multichannel reset')

    rst_fifo_parser = rst_subparsers.add_parser('fifo', help='toggle fifo reset')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(rst_parser)
    def do_reset(self, args) -> None:
        """Toggle multichannel or AXI-FIFO reset"""
        state = self.read_reg(4) & 0x08200
        if args.subcommand is None:
            self.perror("Invalid subcommand")
        elif args.subcommand == 'multi':
            if 0x200 < state:
                self.write_reg(4, self.read_reg(4) & 0x17FFF)
                self.prsuccess("Multichannel free")
            else:
                self.write_reg(4, self.read_reg(4) | 0x08000)
                self.prsuccess("Multichannel reset")
        elif args.subcommand == 'fifo':
            if state == 0x200 or state == 0x8200:
                self.write_reg(4, self.read_reg(4) & 0x1FDFF)
                self.prsuccess("FIFO free")
            else:
                self.write_reg(4, self.read_reg(4) | 0x00200)
                self.prsuccess("FIFO reset")

    #
    # timeout
    #
    timeout_parser = argparse.ArgumentParser()
    timeout_parser.add_argument('value', type=int, help='shifter maximum timeout (unit=8ns)')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(timeout_parser)
    def do_timeout(self, args) -> None:
        """Set data shifter timout"""
        cleanreg = self.read_reg(4) & ~0x1FF
        if self.checkRange(args.value, 1, 512):
            self.write_reg(4, cleanreg | (args.value-1))
            self.prsuccess(f"Timeout set to {args.value} ({args.value*8}ns)")

    #
    # time to peak
    #
    ttp_parser = argparse.ArgumentParser()
    ttp_parser.add_argument('value', type=int, help='time after trigger to ADC sample (max=4096, unit=8ns)')
    ttp_parser.add_argument('channel', type=int, nargs='*', help='channel (1-19)')
    ttp_parser.add_argument('-a', "--all", action="store_true", help='set for all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(ttp_parser)
    def do_timetopeak(self, args) -> None:
        """Set time to peak for each channel"""
        if self.checkRange(args.value, 1, 4096):
            if args.all:
                for i in range(28, 38):
                    self.write_reg(i, (args.value << 12) | args.value)
                self.prsuccess(f"Time to peak set to {args.value} ({args.value*8}ns) for all channels")
            else:
                for channel in args.channel:
                    chaddress = math.floor((channel-1) / 2) + 28
                    cleanreg = self.read_reg(chaddress)
                    if channel % 2 == 0:
                        self.write_reg(chaddress, (args.value << 12) | (cleanreg & 0xFFF))
                    else:
                        self.write_reg(chaddress, (cleanreg & 0xFFF000) | args.value)

    #
    # time to peak
    #
    delay_parser = argparse.ArgumentParser()
    delay_parser.add_argument('value', type=int, help='added deadtime to each measure (max=4096, unit=8ns)')
    delay_parser.add_argument('channel', type=int, nargs='*', help='channel (1-19)')
    delay_parser.add_argument('-a', "--all", action="store_true", help='set for all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(delay_parser)
    def do_delay(self, args) -> None:
        """Set measures delay for each channel"""
        if self.checkRange(args.value, 1, 255):
            if args.all:
                for i in range(38, 43):
                    self.write_reg(i, (args.value << 24) | (args.value << 16) | (args.value << 8) | args.value)
                self.prsuccess(f"Delay set to {args.value} ({args.value*8}ns) for all channels")
            else:
                for channel in args.channel:
                    reg_index = (channel-1) // 4
                    byte_pos = 3 - ((channel-1) % 4)
                    shift = byte_pos * 8
                    mask = 0xFF << shift
                    original = self.read_reg(reg_index+38)
                    cleared = original & ~mask
                    inserted = (args.value & 0xFF) << shift
                    self.write_reg(reg_index+38, cleared | inserted)

    #
    # trigger window
    #
    window_parser = argparse.ArgumentParser()
    window_parser.add_argument('value', type=int, help='external trigger window (max=4294967295, unit=8ns), 0=OFF')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(window_parser)
    def do_window(self, args) -> None:
        """Set trigger window width"""
        if self.checkRange(args.value, 0, 4294967295):
            self.write_reg(44, args.value)
            self.prsuccess(f"Trigger window set to {args.value} ({args.value*8}ns)")

    #
    # rate threshold
    #
    rate_parser = argparse.ArgumentParser()
    rate_parser.add_argument('value', type=int, help='threshold value for the ratemeter (max=65535)')
    rate_parser.add_argument('channel', type=int, nargs='*', help='channel (1-19)')
    rate_parser.add_argument('-a', "--all", action="store_true", help='set for all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(rate_parser)
    def do_threshold(self, args) -> None:
        """Set rate threshold for each channel"""
        if self.checkRange(args.value, 1, 65535):
            if args.all:
                for i in range(46, 56):
                    self.write_reg(i, (args.value << 16) | args.value)
                self.prsuccess(f"Time to peak set to {args.value} ({args.value*8}ns) for all channels")
            else:
                for channel in args.channel:
                    chaddress = math.floor((channel-1) / 2) + 46
                    cleanreg = self.read_reg(chaddress)
                    print(chaddress)
                    if channel % 2 == 0:
                        self.write_reg(chaddress, (args.value << 16) | (cleanreg & 0xFFFF))
                    else:
                        self.write_reg(chaddress, (cleanreg & 0xFFFF0000) | args.value)

    #
    # house-keeping
    #
    @cmd2.with_category("Monitoring commands")
    def do_hk(self, _) -> None:
        """Show house-keeping registers"""
        self.poutput(f"Temperature: {(self.read_reg(56) >> 12)/100}°C")
        self.poutput(f"Relative humidity: {(self.read_reg(56) & 0xFFF)/100}%")
        self.poutput(f"Power: {'not OK' if self.read_reg(61)&0x2 > 0 else 'OK'}")
        self.poutput(f"Voltage: {'not OK' if self.read_reg(61)&0x1 > 0 else 'OK'}")

    #
    # FIFO regs
    #
    @cmd2.with_category("Monitoring commands")
    def do_fifo(self, _) -> None:
        """Show FIFO registers"""
        self.poutput(f"Data in FIFO: {self.read_reg(43)}, {'FULL' if self.read_reg(3)&0x1 > 0 else 'not FULL'}")

    #
    # enable channel trigger
    #
    enable_trigger_parser = argparse.ArgumentParser()
    enable_trigger_parser.add_argument('value', nargs="*", type=int, help='channel to enable trigger (1-19)')
    enable_trigger_parser.add_argument('-a', "--all", action="store_true", help='enable trigger to all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(enable_trigger_parser)
    def do_enable_trigger(self, args) -> None:
        """Enable channel trigger"""
        if args.all:
            self.write_reg(58, 0X7FFFF)
            self.prsuccess("All channels enabled")
        else:
            for channel in args.value:
                if self.checkRange(channel, 1, 19):
                    self.write_reg(58, self.read_reg(58) | (1 << (channel-1)))
                    self.prsuccess(f"Channel {channel} trigger enabled")

    #
    # disable channel trigger
    #
    disable_trigger_parser = argparse.ArgumentParser()
    disable_trigger_parser.add_argument('value', nargs="*", type=int, help='channel to disable trigger (1-19)')
    disable_trigger_parser.add_argument('-a', "--all", action="store_true", help='disable trigger to all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(disable_trigger_parser)
    def do_disable_trigger(self, args) -> None:
        """Disable channel acquisition"""
        if args.all:
            self.write_reg(58, 0)
            self.prsuccess("All channels disabled")
        else:
            for channel in args.value:
                if self.checkRange(channel, 1, 19):
                    self.write_reg(58, self.read_reg(58) & ~(1 << (channel-1)))
                    self.prsuccess(f"Channel {channel} trigger disabled")

    #
    # enable channel pulser
    #
    enable_pulser_parser = argparse.ArgumentParser()
    enable_pulser_parser.add_argument('value', nargs="*", type=int, help='channel to enable pulser (1-19)')
    enable_pulser_parser.add_argument('-a', "--all", action="store_true", help='enable pulser to all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(enable_pulser_parser)
    def do_enable_pulser(self, args) -> None:
        """Enable channel pulser"""
        if args.all:
            self.write_reg(59, 0X7FFFF)
            self.prsuccess("All channels enabled")
        else:
            for channel in args.value:
                if self.checkRange(channel, 1, 19):
                    self.write_reg(59, self.read_reg(59) | (1 << (channel-1)))
                    self.prsuccess(f"Channel {channel} pulser enabled")

    #
    # disable channel pulser
    #
    disable_pulser_parser = argparse.ArgumentParser()
    disable_pulser_parser.add_argument('value', nargs="*", type=int, help='channel to disable pulser (1-19)')
    disable_pulser_parser.add_argument('-a', "--all", action="store_true", help='disable pulser to all channels')

    @cmd2.with_category("Slow control commands")
    @cmd2.with_argparser(disable_pulser_parser)
    def do_disable_pulser(self, args) -> None:
        """Disable channel acquisition"""
        if args.all:
            self.write_reg(59, 0)
            self.prsuccess("All channels disabled")
        else:
            for channel in args.value:
                if self.checkRange(channel, 1, 19):
                    self.write_reg(59, self.read_reg(59) & ~(1 << (channel-1)))
                    self.prsuccess(f"Channel {channel} pulser disabled")

    #
    # printall
    #
    @cmd2.with_category("Monitoring commands")
    def do_printall(self, _) -> None:
        """Print all the registers"""
        for row in range(8):
            self.poutput(f"Register{(row*8):02}: {self.read_reg(row*8):08x}  Register{(row*8)+1:02}: {self.read_reg((row*8)+1):08x}  "
                         f"Register{(row*8)+2:02}: {self.read_reg((row*8)+2):08x}  Register{(row*8)+3:02}: {self.read_reg((row*8)+3):08x}  "
                         f"Register{(row*8)+4:02}: {self.read_reg((row*8)+4):08x}  Register{(row*8)+5:02}: {self.read_reg((row*8)+5):08x}  "
                         f"Register{(row*8)+6:02}: {self.read_reg((row*8)+6):08x}  Register{(row*8)+7:02}: {self.read_reg((row*8)+7):08x}")

    #
    # monitoring
    #
    mon_parser = argparse.ArgumentParser()
    mon_parser.add_argument('seconds',  type=int, default=1, nargs='?', help='number of seconds')

    @cmd2.with_argparser(mon_parser)
    @cmd2.with_category("Monitoring commands")
    def do_mon(self, args: argparse.Namespace) -> None:
        """Monitor monitored values"""
        for i in range(0, args.seconds):
            ratemeters = []
            for j in range(8, 27):
                ratemeters.append(self.read_reg(j))
            deadtime = self.read_reg(27)
            fifodata = self.read_reg(43)
            temp = (self.read_reg(56) >> 12)/100
            hum = (self.read_reg(56) & 0xFFF)/100
            if i % 10 == 0:
                self.prsuccess(f"-----------------------------          Temperature: {temp}°C   Relative humidity: {hum}%          -----------------------------")
            self.pwarning("Rates (Hz):")
            self.poutput("-------------------------------------------------------------------------------------------------------------------------------")
            self.poutput(f"CH1:  {ratemeters[0]:08},  CH2: {ratemeters[1]:08},  CH3: {ratemeters[2]:08},  CH4: {ratemeters[3]:08},  CH5: {ratemeters[4]:08},  CH6: {ratemeters[5]:08},  CH7: {ratemeters[6]:08},  CH8: {ratemeters[7]:08},")
            self.poutput(f"CH9:  {ratemeters[8]:08}, CH10: {ratemeters[9]:08}, CH11: {ratemeters[10]:08}, CH12: {ratemeters[11]:08}, CH13: {ratemeters[12]:08}, CH14: {ratemeters[13]:08}, CH15: {ratemeters[14]:08}, CH16: {ratemeters[15]:08},")
            self.poutput(f"CH17: {ratemeters[16]:08}, CH18: {ratemeters[17]:08}, CH19: {ratemeters[18]:08}  --  Deadtime: {deadtime:08}  --  FIFO: {fifodata} words ({'FULL' if self.read_reg(3)&0x1 > 0 else 'not FULL'})")
            self.poutput("-------------------------------------------------------------------------------------------------------------------------------")
            time.sleep(1)

    #
    # default
    #
    @with_category("Slow control commands")
    def do_default(self, _) -> None:
        """Set all the registers to their default values"""
        ans = self.read_input("\033[93mWarning: do you want to reset all the regsters to their default values? (Y/n) \033[0m")
        if ans.upper() == "Y" or ans == "":
            with open("defaults.json") as f:
                def_reg = json.load(f)
            for add in def_reg.keys():
                self.poutput(f"Reg{add}: {def_reg[add]} (0X{def_reg[add]:08x})")
                self.write_reg(int(add), def_reg[add])
            self.prsuccess("All registers set to default values")
        else:
            self.prsuccess("Nothing changed")


if __name__ == '__main__':
    app = RunControlApp()
    app.cmdloop()
