#!/usr/bin/env python3
# coding=utf-8

import functools
import argparse
import os
import time
import sys
import cmd2
from hvmodbus import HVModbus
from cmd2.table_creator import (
    Column,
    SimpleTable,
    HorizontalAlignment
)
from typing import (
    List,
)

class HighVoltageApp(cmd2.Cmd):

   def __init__(self, port):
      super().__init__(allow_cli_args=False)
      del cmd2.Cmd.do_edit
      del cmd2.Cmd.do_macro
      del cmd2.Cmd.do_run_pyscript
      del cmd2.Cmd.do_shell
      del cmd2.Cmd.do_shortcuts

      self.port = port
      self.allow_style = cmd2.ansi.STYLE_TERMINAL
      self.prompt = cmd2.ansi.style('HV [] > ', fg='bright_black')

      cmd2.categorize(
         (cmd2.Cmd.do_alias, cmd2.Cmd.do_help, cmd2.Cmd.do_history, cmd2.Cmd.do_quit, cmd2.Cmd.do_set, cmd2.Cmd.do_run_script),
         "General commands" 
      )
   
      self.hv = HVModbus()

   def ansi_print(self, text):
      cmd2.ansi.style_aware_write(sys.stdout, text + '\n')

   # Text styles used in the data
   bright_yellow = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_yellow)
   bright_green = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_green)
   bright_red = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_red)
   bright_cyan= functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_cyan)
   bright_blue = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_blue)
   yellow = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.yellow)
   blue = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_blue)
   alarm_red = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_white, bg=cmd2.ansi.bg.bright_red)

   columns: List[Column] = list()
   columns.append(Column("", width=2))
   columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.CENTER))
   columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))
   columns.append(Column("", width=9, data_horiz_align=HorizontalAlignment.RIGHT))
   columns.append(Column("", width=7, data_horiz_align=HorizontalAlignment.RIGHT))
   columns.append(Column("", width=7, data_horiz_align=HorizontalAlignment.RIGHT))
   columns.append(Column("", width=12, data_horiz_align=HorizontalAlignment.RIGHT))
   columns.append(Column("", width=20, data_horiz_align=HorizontalAlignment.RIGHT))
   columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))
   columns.append(Column("", width=14, data_horiz_align=HorizontalAlignment.CENTER))

   st = SimpleTable(columns, divider_char=None)

   def checkAddress(self, addr):
      return (addr >= 0 and addr <= 20)

   def checkConnection(self):
      if(self.hv.isConnected()):
         return True
      else:
         self.perror(f'HV module not connected - use select command') 
         return False

   def checkVoltageSetRange(value):
      try:
         value = int(value)
      except ValueError as err:
         msg = cmd2.ansi.style(f'invalid value type - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      if value < 0 or value > 1500:
         msg = cmd2.ansi.style(f'min:0 max:1500 - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      return value 

   def checkRateRange(value):
      try:
         value = int(value)
      except ValueError as err:
         msg = cmd2.ansi.style(f'invalid value type - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      if value < 1 or value > 25:
         msg = cmd2.ansi.style(f'min:1 max:25 - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      return value

   def checkLimitVoltageRange(value):
      try:
         value = int(value)
      except ValueError as err:
         msg = cmd2.ansi.style(f'invalid value type - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      if value < 1 or value > 10:
         msg = cmd2.ansi.style(f'min:1 max:10 - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      return value

   def checkLimitCurrentRange(value):
      try:
         value = int(value)
      except ValueError as err:
         msg = cmd2.ansi.style(f'invalid value type - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      if value < 1 or value > 10:
         msg = cmd2.ansi.style(f'min:1 max:10 - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      return value

   def checkLimitTemperatureRange(value):
      try:
         value = int(value)
      except ValueError as err:
         msg = cmd2.ansi.style(f'invalid value type - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      if value < 20 or value > 100:
         msg = cmd2.ansi.style(f'min:20 max:100 - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      return value

   def checkLimitTriptimeRange(value):
      try:
         value = int(value)
      except ValueError as err:
         msg = cmd2.ansi.style(f'invalid value type - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      if value < 1 or value > 1000:
         msg = cmd2.ansi.style(f'min:1 max:1000 - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      return value

   def checkThresholdRange(value):
      try:
         value = int(value)
      except ValueError as err:
         msg = cmd2.ansi.style(f'invalid value type - got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      if value < 0 or value > 2500:
         msg = cmd2.ansi.style(f'min:0 max:2500- got {value}', fg='bright_red')
         raise argparse.ArgumentTypeError(msg)

      return value

   def statusString(self, statusCode):
      if (statusCode == 0):
         return 'UP'
      elif (statusCode == 1):
         return 'DOWN'
      elif (statusCode == 2):
         return 'RUP'
      elif (statusCode == 3):
         return 'RDN'
      elif (statusCode == 4):
         return 'TUP'
      elif (statusCode == 5):
         return 'TDN'
      elif (statusCode == 6):
         return 'TRIP'
      else:
         return 'undef'

   def statusIcon(self, statusCode):
      if (statusCode == 0):
         return cmd2.ansi.style(u'\u25C9', fg='bright_green')
      elif (statusCode == 1):
         return u'\u25C9'
      elif (statusCode == 2):
         return cmd2.ansi.style(u'\u22C0', fg='bright_yellow')
      elif (statusCode == 3):
         return cmd2.ansi.style(u'\u22C1', fg='yellow')
      elif (statusCode == 4):
         return cmd2.ansi.style(u'\u22C0', fg='bright_yellow')
      elif (statusCode == 5):
         return cmd2.ansi.style(u'\u22C1', fg='yellow')
      elif (statusCode == 6):
         return cmd2.ansi.style(u'\u25C9', fg='bright_red')
      else:
         return "undef"

   def alarmString(self, alarmCode):
      msg = ' '
      if (alarmCode == 0):
         return 'none'
      if (alarmCode & 1):
         msg = msg + 'OV '
      if (alarmCode & 2):
         msg = msg + 'UV '
      if (alarmCode & 4):
         msg = msg + 'OC '
      if (alarmCode & 8):
         msg = msg + 'OT '
      return self.alarm_red(msg)

   def printMonitorHeader(self):
      self.ansi_print(self.bright_cyan(self.st.generate_data_row(['','status','Vset','V','I','T','rate UP/DN','limit V/I/T/TRIP','Vref','alarm'])))
      self.ansi_print(self.bright_blue(self.st.generate_data_row(['','','[V]','[V]','[uA]','[°C]','[V/s]/[V/s]','[V]/[uA]/[°C]/[ms]','[mV]',''])))
      
   def printMonitorRow(self):
      status = self.hv.getStatus()
      alarm = self.hv.getAlarm()
      self.ansi_print(self.st.generate_data_row([self.statusIcon(status), self.statusString(status), self.hv.getVoltageSet(), f'{self.hv.getVoltage():.3f}', f'{self.hv.getCurrent():.3f}', self.hv.getTemperature(), self.hv.getRate(), self.hv.getLimit(), self.hv.getVref(), self.alarmString(alarm)]))

   #
   # select
   #
   select_parser = argparse.ArgumentParser()
   select_parser.add_argument('address', type=int, help='modbus address [0...20]')

   @cmd2.with_argparser(select_parser)
   @cmd2.with_category("High Voltage commands")
   def do_select(self, args: argparse.Namespace) -> None:
      """Select modbus address"""
      if(self.checkAddress(args.address)):
         if (self.hv.open(self.port, args.address)):
            self.poutput(f'HV module with address {args.address} selected')
         else:
            self.perror(f'HV module with address {args.address} not present')

         if (self.hv.getAddress() is None):
            self.prompt = cmd2.ansi.style('HV [] > ', fg='bright_black')
         else:
            self.prompt = cmd2.ansi.style(f'HV [{self.hv.getAddress()}] > ', fg='bright_green')
      else:
         self.perror(f'E: modbus address outside boundary - min:0 max:20')

   #
   # rate rampup / rampdown
   #
   rate_parser = cmd2.Cmd2ArgumentParser()
   rate_subparsers = rate_parser.add_subparsers(title='subcommands', help='subcommand help')

   rampup_parser = rate_subparsers.add_parser('rampup', help='rampup rate')
   rampup_parser.add_argument('value', type=checkRateRange, help='ramp up voltage rate [V/s] (min:0 max:25)')

   rampdown_parser = rate_subparsers.add_parser('rampdown', help='rampdown rate')
   rampdown_parser.add_argument('value', type=checkRateRange, help='ramp down voltage rate [V/s] (min:0 max:25)')
   
   def rate_rampup(self, args):
      self.hv.setRateRampup(args.value)

   def rate_rampdown(self, args):
      self.hv.setRateRampdown(args.value)

   rampup_parser.set_defaults(func=rate_rampup)
   rampdown_parser.set_defaults(func=rate_rampdown)

   @cmd2.with_argparser(rate_parser)
   @cmd2.with_category("High Voltage commands")
   def do_rate(self, args):
      """Rate command help"""
      if (self.checkConnection() is False):
         return
      func = getattr(args, 'func', None)
      if func is not None:
         func(self, args)
      else:
         self.do_help('rate')

   #
   # limit current / voltage / temperature / triptime
   #
   limit_parser = cmd2.Cmd2ArgumentParser()
   limit_subparsers = limit_parser.add_subparsers(title='subcommands', help='subcommand help')

   current_parser = limit_subparsers.add_parser('current', help='current limit')
   current_parser.add_argument('value', type=checkLimitCurrentRange, help='current threshold [uA] (min:1 max:10)')

   voltage_parser = limit_subparsers.add_parser('voltage', help='voltage margin +/-')
   voltage_parser.add_argument('value', type=checkLimitVoltageRange, help='voltage margin +/- [V] (min:1 max:10)')

   temperature_parser = limit_subparsers.add_parser('temperature', help='temperature limit')
   temperature_parser.add_argument('value',  type=checkLimitTemperatureRange, help='temperature threshold [°C] (min:20 max:100)')

   triptime_parser = limit_subparsers.add_parser('triptime', help='trip time limit')
   triptime_parser.add_argument('value',  type=checkLimitTriptimeRange, help='trip time threshold [ms] (min:1 max:1000)')

   def limit_current(self, args):
      self.hv.setLimitCurrent(args.value)

   def limit_voltage(self, args):
      self.hv.setLimitVoltage(args.value)

   def limit_temperature(self, args):
      self.hv.setLimitTemperature(args.value)

   def limit_triptime(self, args):
      self.hv.setLimitTriptime(args.value)

   current_parser.set_defaults(func=limit_current)
   voltage_parser.set_defaults(func=limit_voltage)
   temperature_parser.set_defaults(func=limit_temperature)
   triptime_parser.set_defaults(func=limit_triptime)

   @cmd2.with_argparser(limit_parser)
   @cmd2.with_category("High Voltage commands")
   def do_limit(self, args):
      """Limit command help"""
      if (self.checkConnection() is False):
         return
      func = getattr(args, 'func', None)
      if func is not None:
         func(self, args)
      else:
         self.do_help('limit')

   #
   # voltage
   #
   voltage_parser = argparse.ArgumentParser()
   voltage_parser.add_argument('value', type=checkVoltageSetRange, help='voltage level [V] (min:0 max:1500)')
   
   @cmd2.with_argparser(voltage_parser)
   @cmd2.with_category("High Voltage commands")
   def do_voltage(self, args: argparse.Namespace) -> None:
      if (self.checkConnection() is False):
         return
      self.hv.setVoltageSet(args.value)

   #
   # on
   #
   on_parser = argparse.ArgumentParser()

   @cmd2.with_argparser(on_parser)
   @cmd2.with_category("High Voltage commands")
   def do_on(self, args: argparse.Namespace) -> None:
      if (self.checkConnection() is False):
         return
      self.hv.powerOn()

   #
   # off
   # 
   off_parser = argparse.ArgumentParser()

   @cmd2.with_argparser(off_parser)
   @cmd2.with_category("High Voltage commands")
   def do_off(self, args: argparse.Namespace) -> None:
      if (self.checkConnection() is False):
         return
      self.hv.powerOff()

   #
   # reset
   #
   reset_parser = argparse.ArgumentParser()

   @cmd2.with_argparser(reset_parser)
   @cmd2.with_category("High Voltage commands")     
   def do_reset(self, args: argparse.Namespace) -> None:
      if (self.checkConnection() is False):
         return
      self.hv.reset()

   #
   # info
   #
   info_parser = argparse.ArgumentParser()

   @cmd2.with_argparser(info_parser)
   @cmd2.with_category("High Voltage commands") 
   def do_info(self, args: argparse.Namespace) -> None:
      if (self.checkConnection() is False):
         return
      info = self.hv.getInfo()
      self.poutput(f'{"FW ver": <15}: {info[0]}.{info[1]}')
      self.poutput(f'{"PM s/n": <15}: {info[2]}')
      self.poutput(f'{"HVPCB s/n": <15}: {info[3]}')
      self.poutput(f'{"IFPCB s/n": <15}: {info[4]}')
      self.poutput(f'{"DAC threshold": <15}: {self.hv.getThreshold()} mV') 

   #
   # mon
   #
   mon_parser = argparse.ArgumentParser()
   mon_parser.add_argument('seconds',  type=int, default=1, nargs='?', help='number of seconds')

   @cmd2.with_argparser(mon_parser)
   @cmd2.with_category("High Voltage commands") 
   def do_mon(self, args: argparse.Namespace) -> None:
      if (self.checkConnection() is False):
         return
      for i in range(0, args.seconds):
         if (i % 20 == 0):
            self.printMonitorHeader()
         self.printMonitorRow()
         if (args.seconds > 1):
            time.sleep(0.5)

   #
   # probe
   #
   probe_parser = argparse.ArgumentParser()

   @cmd2.with_argparser(probe_parser)
   @cmd2.with_category("High Voltage commands")
   def do_probe(self, args: argparse.Namespace) -> None:
      for addr in range(0,21):
         found = self.hv.probe(self.port, addr)
         if(found):
            self.poutput(cmd2.ansi.style(f'{addr}', fg='bright_green'))
         else:
            self.poutput(cmd2.ansi.style(f'{addr}', fg='bright_red'))

   #
   # threshold
   #
   threshold_parser = argparse.ArgumentParser()
   threshold_parser.add_argument('value', type=checkThresholdRange, help='value in mV (min:0 max:2500)')

   @cmd2.with_argparser(threshold_parser)
   @cmd2.with_category("High Voltage commands")
   def do_threshold(self, args: argparse.Namespace) -> None:
      if (self.checkConnection() is False):
         return
      self.hv.setThreshold(args.value)

if __name__ == '__main__':
   parser = argparse.ArgumentParser()
   parser.add_argument('--port', action='store', type=str, help='serial port device (default: /dev/ttyPS1)', default='/dev/ttyPS1')
   args = parser.parse_args()

   app = HighVoltageApp(args.port)
   app.cmdloop()
