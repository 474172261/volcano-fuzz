import struct
import random
Cmds=""
def FormatCmd(base,type,addr,data):
  return struct.pack("<B",(base)<<4|type)+struct.pack("<I",addr)+data

mapped=[-1,-1,-1]
def IoMap(addr,size=4,mapi=0,lock='l'):
  global Cmds
  if mapi>=3:
    print "iomap num too big!"
  if mapped[mapi] == -1:
    mapped[mapi]=mapi
    mapi=mapi+1
    Cmds+= lock+FormatCmd(mapi+0xa,0xa,addr,struct.pack("<I",size))

def WritePort(port,data,size=4,lock='u'):
  global Cmds
  Cmds+= lock+FormatCmd(size,0,port,struct.pack("<I",data))

def WriteMem(offset,data,base=0,size=4,lock='u'):
  global Cmds
  Cmds+= lock+FormatCmd(size,base+3,offset,struct.pack("<I",data))

def WriteCopy(offset,data,base=0,lock='u'):
  global Cmds
  Cmds+= lock+FormatCmd(0,base+6,offset,data)

def Ri(max,min=0):
  return random.randint(min,max)

def cmd_setup_rings():
  WriteMem(0, 3)
  WriteMem(4, Ri(32,1))#reqRingNumPages
  WriteMem(4, Ri(32,1)) #cmpRingNumPages
  WriteMem(4, 0xeb) # ringsStatePPN low page>>12
  WriteMem(4, 0) # ringsStatePPN high
  for i in range(32):#ringsStatePPN >> 4
    WriteMem(4, Ri(0xffffffff))#low
    WriteMem(4, Ri(0xffffffff))#high
  for i in range(32):#cmpRingPPNs
    WriteMem(4, Ri(0xffffffff))#low
    WriteMem(4, Ri(0xffffffff))#high

def processIO():
  WriteMem(0,2,base=1)# set 0xeb000=2
  WriteMem(0x4018, 0)

def cmd_reset_device():
  WriteMem(0, 5)
  WriteMem(4, Ri(64))#target
  WriteMem(4, Ri(0xff)<<8)#make lun[1]=true,else false
  WriteMem(4, 0)

def cmd_abort():
  WriteMem(0,6)
  WriteMem(4, Ri(0xffffffff))#context low
  WriteMem(4, Ri(0xffffffff))#context high
  WriteMem(4, Ri(0xffffffff))#target
  WriteMem(4, Ri(0xffffffff))

def cmd_setup_msg_ring():
  WriteMem(0, 8)
  WriteMem(4, Ri(16))#numPages
  WriteMem(4, Ri(0xffffffff))#pad
  for i in range(16):# ringsPPNs[16] u64
    WriteMem(4, Ri(0xffffffff)) #low
    WriteMem(4, Ri(0xffffffff)) #high

def runCmds():
  cmds=(1,3,4,5,6,8)# 7 not implement
  cmd=cmds[Ri(5)]
  if cmd==1:#pvscsi_reset_adapter
    cmd_setup_rings()
    processIO()
    WriteMem(0, 1)
  elif cmd==3:#pvscsi_on_cmd_setup_rings
    cmd_setup_rings()
    processIO()
  elif cmd==4:
    WriteMem(0, 4)
  elif cmd==5:
    cmd_reset_device()
  elif cmd==6:
    cmd_setup_rings()
    processIO()
    cmd_abort()
  else:
    cmd_setup_rings()
    cmd_setup_msg_ring()

def pvscsiFuzz():
  cases=(0,4,0x3014,0x4018)#0x100c,0x2010,
  off=cases[Ri(3)]
  if off<5:
    runCmds()
  else:
    cmd_setup_rings()
    processIO()
  return Cmds
# cmd=pvscsiFuzz()
# for i in range(len(cmd)/10):
#   print cmd[i*10:i*10+10].encode('hex')
