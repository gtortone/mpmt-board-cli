#!/usr/bin/env python3
# coding=utf-8

import argparse
import time
import sys
import cmd2
import getpass
import numpy as np
from hvmodbus import HVModbus
from cmd2.table_creator import (
    Column,
    SimpleTable,
    HorizontalAlignment
)
from typing import (
    List,
)

HV_PASS = 'hv4all'

class HighVoltageApp(cmd2.Cmd):

    def __init__(self, param):
        super().__init__(allow_cli_args=False)
        del cmd2.Cmd.do_edit
        del cmd2.Cmd.do_macro
        del cmd2.Cmd.do_run_pyscript
        del cmd2.Cmd.do_shell
        del cmd2.Cmd.do_shortcuts

        self.param = param
        self.port = self.param.port
        self.allow_style = cmd2.ansi.allow_style
        self.allow_style = 'Terminal'
        self.prompt = cmd2.ansi.style(f'HV:{self.param.mode} [] > ', fg=cmd2.ansi.Fg.DARK_GRAY)

        cmd2.categorize(
            (cmd2.Cmd.do_alias, cmd2.Cmd.do_help, cmd2.Cmd.do_history, cmd2.Cmd.do_quit, cmd2.Cmd.do_set, cmd2.Cmd.do_run_script),
            "General commands"
        )

        self.hv = HVModbus(param)

    columns: List[Column] = list()
    columns.append(Column("", width=2))
    columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.CENTER))
    columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))
    columns.append(Column("", width=9, data_horiz_align=HorizontalAlignment.RIGHT))
    columns.append(Column("", width=7, data_horiz_align=HorizontalAlignment.RIGHT))
    columns.append(Column("", width=7, data_horiz_align=HorizontalAlignment.RIGHT))
    columns.append(Column("", width=12, data_horiz_align=HorizontalAlignment.RIGHT))
    columns.append(Column("", width=20, data_horiz_align=HorizontalAlignment.RIGHT))
    columns.append(Column("", width=13, data_horiz_align=HorizontalAlignment.RIGHT))
    columns.append(Column("", width=14, data_horiz_align=HorizontalAlignment.CENTER))

    st = SimpleTable(columns, divider_char=None)

    def checkRange(self, value, minVal, maxVal):
        if value < minVal or value > maxVal:
            self.perror(f'Error: value out of range {minVal}-{maxVal} - got {value}')
            return False
        return True

    def checkLength(self, value, maxVal):
        if len(value) > maxVal:
            self.perror(f'ERROR: serial longer than {maxVal} chars - got {len(value)} chars')
            return False
        return True

    def checkAddress(self, addr):
        return 0 <= addr <= 20

    def checkConnection(self):
        if self.hv.isConnected():
            return True
        else:
            self.perror(f'HV module not connected - use select command')
            return False

    def checkPassword(self, password):
        return password == HV_PASS

    def select_address(self, address):
        if self.checkAddress(address):
            if self.hv.open(address):
                self.psuccess(f'HV module with address {address} selected')
            else:
                self.perror(f'HV module with address {address} not present')

            if self.hv.getAddress() is None:
                self.prompt = cmd2.ansi.style(f'HV:{self.param.mode} [] > ', fg=cmd2.ansi.Fg.DARK_GRAY)
            else:
                self.prompt = cmd2.ansi.style(f'HV:{self.param.mode} [{self.hv.getAddress()}] > ', fg=cmd2.ansi.Fg.LIGHT_GREEN)
        else:
            self.perror(f'E: modbus address outside boundary - min:1 max:20')

    def statusString(self, statusCode):
        if statusCode == 0:
            return 'UP'
        elif statusCode == 1:
            return 'DOWN'
        elif statusCode == 2:
            return 'RUP'
        elif statusCode == 3:
            return 'RDN'
        elif statusCode == 4:
            return 'TUP'
        elif statusCode == 5:
            return 'TDN'
        elif statusCode == 6:
            return 'TRIP'
        else:
            return 'undef'

    def statusIcon(self, statusCode):
        if statusCode == 0:
            return self.psuccess(u'\u25C9')
        elif statusCode == 1:
            return u'\u25C9'
        elif statusCode == 2:
            return self.psuccess(u'\u22C0')
        elif statusCode == 3:
            return self.pwarning(u'\u22C1')
        elif statusCode == 4:
            return self.psuccess(u'\u22C0')
        elif statusCode == 5:
            return self.pwarning(u'\u22C1')
        elif statusCode == 6:
            return self.psuccess(u'\u25C9')
        else:
            return "undef"

    def alarmString(self, alarmCode):
        msg = ' '
        if alarmCode == 0:
            return 'none'
        if alarmCode & 1:
            msg = msg + 'OV '
        if alarmCode & 2:
            msg = msg + 'UV '
        if alarmCode & 4:
            msg = msg + 'OC '
        if alarmCode & 8:
            msg = msg + 'OT '
        return cmd2.ansi.style(msg, fg=cmd2.ansi.Fg.WHITE, bg=cmd2.ansi.Bg.LIGHT_RED)

    def printMonitorHeader(self):
        self.poutput(cmd2.ansi.style(self.st.generate_data_row(['','status','Vset','V','I','T','rate UP/DN','limit V/I/T/TRIP','trigger thr','alarm']), fg=cmd2.ansi.Fg.LIGHT_CYAN))
        self.poutput(cmd2.ansi.style(self.st.generate_data_row(['','','[V]','[V]','[uA]','[°C]','[V/s]/[V/s]','[V]/[uA]/[°C]/[s]','[mV]','']), fg=cmd2.ansi.Fg.LIGHT_BLUE))

    def printMonitorRow(self):
        monData = self.hv.readMonRegisters()
        if monData is None:
            self.perror('Error reading registers')
        else:
            self.poutput(self.st.generate_data_row([self.statusIcon(monData['status']), self.statusString(monData['status']), monData['Vset'], f'{monData["V"]:.3f}', f'{monData["I"]:.3f}', monData['T'], f'{monData["rateUP"]}/{monData["rateDN"]}', f'{monData["limitV"]}/{monData["limitI"]}/{monData["limitT"]}/{monData["limitTRIP"]}', monData['threshold'], self.alarmString(monData['alarm'])]))

    #
    # select
    #
    select_parser = argparse.ArgumentParser()
    select_parser.add_argument('address', type=int, help='modbus address [1...20]')

    @cmd2.with_argparser(select_parser)
    @cmd2.with_category("High Voltage commands")
    def do_select(self, args: argparse.Namespace) -> None:
        """Select modbus address"""
        self.select_address(args.address)

    #
    # rate rampup / rampdown
    #
    rate_parser = cmd2.Cmd2ArgumentParser()
    rate_subparsers = rate_parser.add_subparsers(title='subcommands')

    rampup_parser = rate_subparsers.add_parser('rampup', help='rampup rate')
    rampup_parser.add_argument('value', type=int, help='ramp up voltage rate [V/s] (min:1 max:25)')

    rampdown_parser = rate_subparsers.add_parser('rampdown', help='rampdown rate')
    rampdown_parser.add_argument('value', type=int, help='ramp down voltage rate [V/s] (min:1 max:25)')

    def rate_rampup(self, args):
        if self.checkRange(args.value, 1, 25): self.hv.setRateRampup(args.value)

    def rate_rampdown(self, args):
        if self.checkRange(args.value, 1, 25): self.hv.setRateRampdown(args.value)

    rampup_parser.set_defaults(func=rate_rampup)
    rampdown_parser.set_defaults(func=rate_rampdown)

    @cmd2.with_argparser(rate_parser)
    @cmd2.with_category("High Voltage commands")
    def do_rate(self, args):
        """Change the rampup/rampdown values [V/s]"""
        if self.checkConnection() is False:
            return
        func = getattr(args, 'func', None)
        if func is not None:
            func(self, args)

    #
    # limit current / voltage / temperature / triptime
    #
    limit_parser = cmd2.Cmd2ArgumentParser()
    limit_subparsers = limit_parser.add_subparsers(title='subcommands')

    current_parser = limit_subparsers.add_parser('current', help='current limit')
    current_parser.add_argument('value', type=int, help='current threshold [uA] (min:1 max:10)')

    voltage_parser = limit_subparsers.add_parser('voltage', help='voltage margin +/-')
    voltage_parser.add_argument('value', type=int, help='voltage margin +/- [V] (min:1 max:20)')

    temperature_parser = limit_subparsers.add_parser('temperature', help='temperature limit')
    temperature_parser.add_argument('value', type=int, help='temperature threshold [°C] (min:20 max:70)')

    triptime_parser = limit_subparsers.add_parser('triptime', help='trip time limit')
    triptime_parser.add_argument('value', type=int, help='trip time threshold [s] (min:1 max:1000)')

    def limit_current(self, args):
        if self.checkRange(args.value, 1, 10): self.hv.setLimitCurrent(args.value)

    def limit_voltage(self, args):
        if self.checkRange(args.value, 1, 20): self.hv.setLimitVoltage(args.value)

    def limit_temperature(self, args):
        if self.checkRange(args.value, 20, 70): self.hv.setLimitTemperature(args.value)

    def limit_triptime(self, args):
        if self.checkRange(args.value, 1, 1000): self.hv.setLimitTriptime(args.value)

    current_parser.set_defaults(func=limit_current)
    voltage_parser.set_defaults(func=limit_voltage)
    temperature_parser.set_defaults(func=limit_temperature)
    triptime_parser.set_defaults(func=limit_triptime)

    @cmd2.with_argparser(limit_parser)
    @cmd2.with_category("High Voltage commands")
    def do_limit(self, args):
        """Set current/voltage/tempreature/trip time limit"""
        if self.checkConnection() is False:
            return
        func = getattr(args, 'func', None)
        if func is not None:
            func(self, args)

    #
    # voltage
    #
    voltage_parser = argparse.ArgumentParser()
    voltage_parser.add_argument('value', type=int, help='voltage level [V] (min:25 max:1500)')

    @cmd2.with_argparser(voltage_parser)
    @cmd2.with_category("High Voltage commands")
    def do_voltage(self, args: argparse.Namespace) -> None:
        """Set voltage"""
        if self.checkConnection() is False:
            return
        if self.checkRange(args.value, 25, 1500): self.hv.setVoltageSet(args.value)

    #
    # on
    #
    @cmd2.with_category("High Voltage commands")
    def do_on(self, _) -> None:
        """Turn on HV"""
        if self.checkConnection() is False:
            return
        self.hv.powerOn()

    #
    # off
    #
    @cmd2.with_category("High Voltage commands")
    def do_off(self, _) -> None:
        """Turn off HV"""
        if self.checkConnection() is False:
            return
        self.hv.powerOff()

    #
    # reset
    #
    @cmd2.with_category("High Voltage commands")
    def do_reset(self, _) -> None:
        """Reset alarms"""
        if self.checkConnection() is False:
            return
        self.hv.reset()

    #
    # info
    #
    @cmd2.with_category("High Voltage commands")
    def do_info(self, _) -> None:
        """Print board info"""
        if self.checkConnection() is False:
            return
        info = self.hv.getInfo()
        (m,q,t) = self.hv.readCalibRegisters()
        self.poutput(f'{"FW ver": <25}: {info[0]}')
        self.poutput(f'{"PMT s/n": <25}: {info[1]}')
        self.poutput(f'{"HV s/n": <25}: {info[2]}')
        self.poutput(f'{"FEB s/n": <25}: {info[3]}')
        self.poutput(f'{"Device ID s/n": <25}: {info[4]}')
        self.poutput(f'{"Vref": <25}: {self.hv.getVref()} mV')
        self.poutput(f'{"Calibration slope": <25}: {m}')
        self.poutput(f'{"Calibration offset": <25}: {q}')
        self.poutput(f'{"Calibration discrim.": <25}: {int(t)} mV')

    #
    # mon
    #
    mon_parser = argparse.ArgumentParser()
    mon_parser.add_argument('seconds',  type=int, default=1, nargs='?', help='number of seconds')

    @cmd2.with_argparser(mon_parser)
    @cmd2.with_category("High Voltage commands")
    def do_mon(self, args: argparse.Namespace) -> None:
        """Print monitored values"""
        if self.checkConnection() is False:
            return
        for i in range(0, args.seconds):
            if i % 20 == 0:
                self.printMonitorHeader()
            self.printMonitorRow()
            if args.seconds > 1:
                time.sleep(1)

    #
    # probe
    #
    @cmd2.with_category("High Voltage commands")
    def do_probe(self, _) -> None:
        """Probe addresses 1 to 20"""
        for addr in range(1,21):
            found = self.hv.open(addr)
            if found:
                self.psuccess(f'{addr}')
            else:
                self.perror(f'{addr}')

    #
    # threshold
    #
    threshold_parser = argparse.ArgumentParser()
    threshold_parser.add_argument('value', type=int, help='value in mV (min:0 max:2500)')

    @cmd2.with_argparser(threshold_parser)
    @cmd2.with_category("High Voltage commands")
    def do_threshold(self, args: argparse.Namespace) -> None:
        """Set threshold"""
        if self.checkConnection() is False:
            return
        if self.checkPassword(getpass.getpass()):
            if self.checkRange(args.value, 0, 2500): self.hv.setThreshold(args.value)
        else:
            self.perror(f'password not correct')
    #
    # serial
    #
    serial_parser = argparse.ArgumentParser()
    serial_subparsers = serial_parser.add_subparsers(title='subcommands')

    pmt_parser = serial_subparsers.add_parser('pmt', help='PMT')
    pmt_parser.add_argument('sn', type=str, help='serial number (max 12 char)')

    hv_parser = serial_subparsers.add_parser('hv', help='HV')
    hv_parser.add_argument('sn', type=str, help='serial number (max 12 char)')

    feb_parser = serial_subparsers.add_parser('feb', help='FEB')
    feb_parser.add_argument('sn', type=str, help='serial number (max 12 char)')

    def serial_pmt(self, args):
        if self.checkConnection() is False:
            return
        if self.checkLength(args.value, 12): self.hv.setPMTSerialNumber(args.sn)

    def serial_hv(self, args):
        if self.checkConnection() is False:
            return
        if self.checkLength(args.value, 12): self.hv.setHVSerialNumber(args.sn)

    def serial_feb(self, args):
        if self.checkConnection() is False:
            return
        if self.checkLength(args.value, 12): self.hv.setFEBSerialNumber(args.sn)

    pmt_parser.set_defaults(func=serial_pmt)
    hv_parser.set_defaults(func=serial_hv)
    feb_parser.set_defaults(func=serial_feb)

    @cmd2.with_argparser(serial_parser)
    @cmd2.with_category("High Voltage commands")
    def do_serial(self, args):
        """Set serial numbers for PMT/HV/FEB"""
        if self.checkConnection() is False:
            return
        func = getattr(args, 'func', None)
        if func is not None:
            if self.checkPassword(getpass.getpass()):
                func(self, args)
            else:
                self.perror(f'password not correct')

    #
    # address
    #
    address_parser = argparse.ArgumentParser()
    address_parser.add_argument('value', type=int, help='modbus address (min:1 max:20)')

    @cmd2.with_argparser(address_parser)
    @cmd2.with_category("High Voltage commands")
    def do_address(self, args: argparse.Namespace) -> None:
        """Change selected board address"""
        if self.checkConnection() is False:
            return
        if self.checkPassword(getpass.getpass()):
            if self.checkRange(args.value, 1, 20):
                self.hv.setModbusAddress(args.value)
                time.sleep(0.5)
                self.select(args.value)
            else:
                return
        else:
            self.perror(f'password not correct')

    #
    # slope
    #
    slope_parser = argparse.ArgumentParser()
    slope_parser.add_argument('value', type=float, help='calibration slope value')

    @cmd2.with_argparser(slope_parser)
    @cmd2.with_category("High Voltage commands")
    def do_slope(self, args: argparse.Namespace) -> None:
        """Change calibration slope"""
        if self.checkConnection() is False:
            return
        if self.checkPassword(getpass.getpass()):
            self.hv.writeCalibSlope(args.value)
        else:
            self.perror(f'password not correct')

    #
    # offset
    #
    offset_parser = argparse.ArgumentParser()
    offset_parser.add_argument('value', type=float, help='calibration offset value')

    @cmd2.with_argparser(offset_parser)
    @cmd2.with_category("High Voltage commands")
    def do_offset(self, args: argparse.Namespace) -> None:
        """Change calibration offset"""
        if self.checkConnection() is False:
            return
        if self.checkPassword(getpass.getpass()):
            self.hv.writeCalibOffset(args.value)
        else:
            self.perror(f'password not correct')

    #
    # discr
    #
    discr_parser = argparse.ArgumentParser()
    discr_parser.add_argument('value', type=int, help='calibration discriminator value')

    @cmd2.with_argparser(discr_parser)
    @cmd2.with_category("High Voltage commands")
    def do_discr(self, args: argparse.Namespace) -> None:
        """Set discr"""
        if self.checkConnection() is False:
            return
        if self.checkPassword(getpass.getpass()):
            self.hv.writeCalibDiscr(args.value)
        else:
            self.perror(f'password not correct')


    #
    # calibration
    #
    @cmd2.with_category("High Voltage commands")
    def do_calibration(self, _) -> None:
        """Start calibration procedure"""
        if self.checkConnection() is False:
            return

        if not self.checkPassword(getpass.getpass()):
            self.perror(f'password not correct')
            return

        ans = input(self.pwarning('WARNING: calibration is a time consuming task - confirm (Y/N) '))
        if str(ans).upper() != 'Y':
            return

        ans = input(self.pwarning('WARNING: do you agree to erase current calibration values ? (Y/N) '))
        if str(ans).upper() != 'Y':
            return

        self.hv.writeCalibSlope(1)
        self.hv.writeCalibOffset(0)

        Vexpect = [25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400]
        Vread = []

        self.poutput('set fast rampup/rampdown rate (25 V/s)')
        self.hv.setRateRampup(25)
        self.hv.setRateRampdown(25)

        self.poutput('start calibration with status=DOWN Vset=10V')
        self.hv.setVoltageSet(10)
        self.hv.powerOff()
        self.poutput(f'waiting for voltage < {Vexpect[0]}')
        self.printMonitorHeader()
        self.printMonitorRow()
        while self.hv.getVoltage() > Vexpect[0]:
            self.printMonitorRow()
            time.sleep(1)

        self.psuccess('turn on high voltage')
        self.hv.powerOn()
        for v in Vexpect:
            self.psuccess(f"Vset = {v}V")
            self.hv.setVoltageSet(v)
            time.sleep(1)
            self.poutput('waiting for voltage level')
            self.printMonitorHeader()
            self.printMonitorRow()
            while True:
                if self.statusString(self.hv.getStatus()) != 'UP':
                    self.printMonitorRow()
                    time.sleep(1)
                    continue
                else:
                    self.printMonitorRow()
                    self.poutput(f'Vset = {v}V reached - collecting samples')
                    # wait for voltage leveling
                    time.sleep(2)
                    Vtemp = []
                    self.printMonitorHeader()
                    for _ in range(0,10):
                        self.printMonitorRow()
                        Vtemp.append(self.hv.getVoltage())
                        time.sleep(0.5)
                    Vmeas = np.array(Vtemp)
                    # delete min/max elements
                    Vmeas.sort()
                    Vmeas = np.delete(Vmeas, 0)
                    Vmeas = np.delete(Vmeas, len(Vmeas)-1)
                    Vread.append(Vmeas.mean())
                    self.poutput(f'{Vmeas}')
                    self.poutput(f'mean = {Vmeas.mean()}')
                    break

        self.poutput(f'Vexpect => {Vexpect}')
        self.poutput(f'Vread => {Vread}')

        x = np.array(Vread)
        y = np.array(Vexpect)
        # assemble matrix A
        A = np.vstack([x, np.ones(len(x))]).T
        # turn y into a column vector
        y = y[:, np.newaxis]
        # direct least square regression
        alpha = np.dot((np.dot(np.linalg.inv(np.dot(A.T,A)),A.T)),y)
        self.poutput(cmd2.ansi.style(f'slope = {alpha[0][0]} , offset = {alpha[1][0]}', fg=cmd2.ansi.Fg.LIGHT_CYAN))

        # write calibration registers
        ans = input(self.pwarning('WARNING: do you want to write new calibration values ? (Y/N) '))
        if str(ans).upper() == 'Y':
            self.hv.writeCalibSlope(float(alpha[0][0]))
            self.hv.writeCalibOffset(float(alpha[1][0]))
            self.poutput('OK')

        self.poutput('stop calibration with status=DOWN Vset=10V')
        self.hv.setVoltageSet(10)
        self.hv.powerOff()

        self.psuccess('calibration DONE!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default='rtu', const='rtu', nargs='?', choices=['rtu', 'tcp'], help='set modbus interface (default: %(default)s)')
    parser.add_argument('--port', action='store', type=str, help='serial port device (default: /dev/ttyPS2)', default='/dev/ttyPS2')
    parser.add_argument('--host', action='store', type=str, help='mbusd hostname (default: localhost)', default='localhost')
    args = parser.parse_args()

    app = HighVoltageApp(args)
    app.cmdloop()
