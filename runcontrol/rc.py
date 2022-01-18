#!/usr/bin/env python3
# coding=utf-8

import argparse
import os
import sys
import cmd2
import mmap
from cmd2.table_creator import (Column, BorderedTable, HorizontalAlignment)

class RunControlApp(cmd2.Cmd):

   def __init__(self):
      super().__init__()
      del cmd2.Cmd.do_edit
      del cmd2.Cmd.do_macro
      del cmd2.Cmd.do_run_pyscript
      del cmd2.Cmd.do_shell
      del cmd2.Cmd.do_shortcuts

      self.allow_style = cmd2.ansi.STYLE_TERMINAL
      self.prompt = 'RC> '
      self.prompt = cmd2.ansi.style(self.prompt, fg='bright_green')

      self.maxRegisterAddress = 50

      self.columns: List[Column] = list()
      self.columns.append(Column("31...24", width=10, header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
      self.columns.append(Column("23...16", width=10, header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
      self.columns.append(Column("15...8", width=10, header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
      self.columns.append(Column("7...0", width=10, header_horiz_align=HorizontalAlignment.CENTER, data_horiz_align=HorizontalAlignment.CENTER))
      self.bt = BorderedTable(self.columns)

      try:
         self.fid = open('/dev/uio0', 'r+b', 0)
      except:
         print("E: UIO device /dev/uio0 not found")
         sys.exit(-1)
      self.regs = mmap.mmap(self.fid.fileno(), 0x10000)

      cmd2.categorize(
         (cmd2.Cmd.do_alias, cmd2.Cmd.do_help, cmd2.Cmd.do_history, cmd2.Cmd.do_quit, cmd2.Cmd.do_set, cmd2.Cmd.do_run_script),
         "General commands" 
      )

   def auto_int(x):
      return int(x, 0)

   def checkRegBoundary(self, addr):
      if (addr < 0 or addr > self.maxRegisterAddress):
         return False
      return True

   # read UIO register parser
   read_parser = argparse.ArgumentParser()
   read_parser.add_argument('address', type=auto_int, help='decimal or hexadecimal (prefix 0x)')

   @cmd2.with_argparser(read_parser)
   @cmd2.with_category("UIO commands")
   def do_read(self, args: argparse.Namespace) -> None:
      """Read UIO register"""
      if (self.checkRegBoundary(args.address)):
         value = int.from_bytes(self.regs[args.address*4:(args.address*4)+4], byteorder='little')
         self.poutput(f'0x{value:08x} ({value})')
      else:
         self.perror(f'E: register address outside boundary - min:0 max:{self.maxRegisterAddress}')

   # write UIO register parser
   write_parser = argparse.ArgumentParser()
   write_parser.add_argument('address', type=auto_int, help='decimal or hexadecimal (prefix 0x)')
   write_parser.add_argument('value', type=auto_int, help='decimal or hexadecimal (prefix 0x)')

   @cmd2.with_argparser(write_parser)
   @cmd2.with_category("UIO commands")
   def do_write(self, args: argparse.Namespace) -> None:
      """Write UIO register"""
      if (self.checkRegBoundary(args.address)):
         try:
            self.regs[args.address*4:(args.address*4)+4] = int.to_bytes(args.value, 4, byteorder='little')
         except:
            self.perror(f'E: write register error')
      else:
         self.perror(f'E: register address outside boundary - min:0 max:{self.maxRegisterAddress}')

   # dump UIO register
   dump_parser = argparse.ArgumentParser()
   dump_parser.add_argument('address', type=auto_int, help='decimal or hexadecimal (prefix 0x)')

   @cmd2.with_argparser(dump_parser)
   @cmd2.with_category("UIO commands")
   def do_dump(self, args: argparse.Namespace) -> None:
      """Dump UIO register"""
      if (self.checkRegBoundary(args.address)):
         value = self.regs[args.address*4:(args.address*4)+4]
         data_list: List[List[Any]] = list()
         data_list.append([ format(value[3], '08b'), format(value[2], '08b'), format(value[1], '08b'), format(value[0], '08b') ])
         data_list.append([ f'0x{value[3]:02x}', f'0x{value[2]:02x}', f'0x{value[1]:02x}', f'0x{value[0]:02x}', ])
         table = self.bt.generate_table(data_list)
         self.poutput(table)
      else:
         self.perror(f'E: register address outside boundary - min:0 max:{self.maxRegisterAddress}')

if __name__ == '__main__':
   app = RunControlApp()
   app.cmdloop()
