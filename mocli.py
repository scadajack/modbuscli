#!/usr/bin/env python

import argparse
import functools

'''
Command Line Wrapper around pymodbus

Known Issues:
  Writing Integer Values: if the first value in a --values input is a negative 
  value, the parser interprets it incorrectly as an option flag. This can be 
  avoided if the space is removed between the -v or --values flag and the 
  values that follow.
'''



def stringBool(val):
  uval = val.upper()
  if uval in ['1','T','TRUE']:
    return True
  elif uval in ['0','F','FALSE']:
    return False
  else:
    return None

def arrayStringBools(valarr):
  result = [stringBool(item) for item in valarr]
  return result

# String to Int works as expected except for when value is out of signed or 
# unsigned Modbus Word (2 Bytes) range. In this case it will return None. If a 
# negative number is provided, it is converted to the equivalent unsigned Word 
# value silently.
def stringToInt(val):
  intval = int(val)
  if intval < -0xFFFF or intval > 0xFFFF:
    return None
  elif intval < 0:
    return 0x10000 + intval
  else:
    return intval 


def arrayStringInts(valarr):
  return [stringToInt(item) for item in valarr]

parser = argparse.ArgumentParser(prog='ReadHTcp')

parser.add_argument('method', choices=['tcp','udp','rtu','serial'], default='tcp')
parser.add_argument('-a','--address',type=int)
parser.add_argument('-c','--count',type=int,default=1)
parser.add_argument('-v','--values',type=lambda s: [item for item in list(map(lambda t: t.strip(),s.split(',')))])

parser.add_argument('-i','--ip',default='127.0.0.1')
parser.add_argument('-p','--port',default=502,type=int)
parser.add_argument('-u','--unit',type=int,default='0')
# Arguments for Serial Clients
# timeout is in seconds
parser.add_argument('-t', '-timeout',type=int,default=3)
parser.add_argument('--stopbits',choices=[0,1,2],default=1)
parser.add_argument('--bytesize',choices=[5,6,7,8],default=8)
parser.add_argument('--parity',choices=['N','E','O'])
parser.add_argument('--baudrate',type=int,default=9600)

# Datastore Arguments
parser.add_argument('--zeromode',action='store_true')

parser.add_argument('-r','--repeat',type=int,default=1)
parser.add_argument('-f','--function',choices=['rcs','wcs','wc','rds','rhs','whs','wh','ris','rwh','mwh','read-coils','write-coils','write_coil','read-discretes','read-holdings','write-holdings','write-holding','read-inputs','read-write-registers','mask-write-register'])

parser.add_argument('-d','--debug',action='store_true')

kargs, uargs = parser.parse_known_args()

duargs = {}

for s in uargs:
  key,val = s.split('=')
  duargs[key]=val

if kargs.debug:
  print('dict',kargs.__dict__)
  print('debug', kargs.debug)
  print('Known: ', kargs)
  print('Unknown: ',uargs)
  print('Unknown Dict: ',duargs)
  quit()

client = None

try:
  if kargs.method == 'tcp':
    from pymodbus.client.sync import ModbusTcpClient

    client = ModbusTcpClient(kargs.ip,port=kargs.port,unit_id=kargs.unit)

  elif kargs.method == 'rtu':
    from pymodbus.client.sync import ModbusSeriaClient

    client = ModbusRtuClient(kargs.method, port=kargs.port, stopbits=kargs.stopbits,bytesize=kargs.bytesize,parity=kargs.parity,baudrate=kargs.baudrate,timeout=kargs.timeout)

  if client != None:
    display_prefix = ''
    function_result = None
    write_result = None
    for x in range(kargs.repeat):
      if kargs.function in ['rcs','read-coils']:
        read = client.read_coils(kargs.address,kargs.count,unit=kargs.unit)
        function_result=read.bits
        display_prefix = 'Read Coils'

      elif kargs.function in ['rds','read-discretes']:
        read = client.read_discrete_inputs(kargs.address,kargs.count,unit=kargs.unit)
        function_result=read.bits
        display_prefix = 'Read Discretes'

      elif kargs.function in ['ris','read-inputs']:
        read = client.read_input_registers(kargs.address,kargs.count,unit=kargs.unit)
        function_result=read.registers
        display_prefix = 'Read Input Registers'

      elif kargs.function in ['rhs','read-holding']:
        read = client.read_holding_registers(kargs.address,kargs.count,unit=kargs.unit)
        function_result = read.registers
        display_prefix = 'Read Holding'

      elif kargs.function in ['wc','write-coil']:
        result = client.write_coil(kargs.address,stringBool(kargs.values[0]),unit=kargs.unit)
        write_result = result
        display_prefix = 'Write Coil'

      elif kargs.function in ['wcs','write-coils']:
        coil_values = arrayStringBools(kargs.values)
        result = client.write_coils(kargs.address,coil_values,unit=kargs.unit)
        write_result = result
        display_prefix = 'Write Coils'

      elif kargs.function in ['wh','write-holding']:
        result = client.write_register(kargs.address,stringToInt(kargs.values[0]),unit=kargs.unit)
        write_result = result
        display_prefix = 'Write Holding Register'

      elif kargs.function in ['whs','write-holdings']:
#        print('-------> Values: ' +str(arrayStringInts(kargs.values)))
        result = client.write_registers(kargs.address,arrayStringInts(kargs.values),unit=kargs.unit)
        write_result = result
        display_prefix = 'Write Holding Registers'

      else:
        print('Function "%s" is not yet implemented in this wrapper. Exiting' % kargs.function)
        quit() 

# Display results
      if function_result != None:
        print(display_prefix + ' #%s' % x,functools.reduce(lambda x,y: str(x)+ ',' + str(y),function_result[:kargs.count]))

      if write_result != None:
        print(display_prefix + ' #%s' % x, write_result)

finally:
  if client != None:
    client.close()
 
