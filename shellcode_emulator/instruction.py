import os
import sys

import struct
import traceback
import logging
import capstone

from unicorn import *
from unicorn.x86_const import *

import shellcode_emulator.utils

class Tool:
    def __init__(self, emulator):
        self.Emulator = emulator
        self.uc = emulator.uc
        self.LastCodeAddress = 0
        self.LastCodeSize = 0
        self.Start = 0
        self.End = 0

    def SetCodeRange(self, start, end):
        self.Start = start
        self.End = end

    def Disassemble(self, code, address):
        if self.Emulator.Arch == 'x86':
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        elif self.Emulator.Arch == 'AMD64':
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        return md.disasm(code, address)

    def DumpDisasm(self, address, size, resolve_symbol = False, dump_instruction_count = 1):
        code = self.uc.mem_read(address, size)

        try:            
            disasm_list = self.Disassemble(code, address)
        except:
            traceback.print_exc(file = sys.stdout)
            return

        i = 0
        offset = 0
        for instruction in disasm_list:
            symbol_str = ''
            if self.Emulator.Debugger:
                try:
                    symbol_str = self.Emulator.Debugger.ResolveSymbol(instruction.address) + ':\t'
                except:
                    pass
                    

            code_offset = 0
            if self.Start <= instruction.address and instruction.address <= self.End:
                code_offset = instruction.address - self.Start
                
            if code_offset>0:
                address_str = '+%.8X: ' % (code_offset)
            else:
                address_str = ' %.8X: ' % (instruction.address)

            print('%s%s%s\t%s\t%s' % (symbol_str, address_str, utils.Tool.DumpHex(code[offset:offset+instruction.size]), instruction.mnemonic, instruction.op_str))

            offset += instruction.size
            i += 1

            if i >= dump_instruction_count:
                break

    def DumpContext(self, dump_registers = True, dump_previous_eip = False):
        self.DumpDisasm(self.uc.reg_read(self.Emulator.GetReg("eip")), 10)

        if dump_registers:
            self.Emulator.Register.DumpRegisters()

        if dump_previous_eip and self.LastCodeAddress>0:
            print('> Last EIP before this instruction:')
            self.DumpDisasm(self.LastCodeAddress, self.LastCodeSize)
