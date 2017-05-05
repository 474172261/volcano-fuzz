import struct
fp=open('last_one_cmds','rb')
Cmds=""
data=fp.read(10)
while data:
  cmd_types=int(data[1:2])
  cmd_size=(cmd_types&0xf0)>>4
  cmd_type=(cmd_types&0xf)
  cmd_addr=struct.unpack('<I',each[2:6])[0]
  cmd_val=cmd_addr=struct.unpack('<I',each[6:])[0]
  if cmd_type==0:
    if cmd_size==4:
      print '  outl('+str(cmd_val)+','+str(cmd_addr)+');'
    else:
      print '  outb('+str(cmd_val)+','+str(cmd_addr)+');'
  elif cmd_type==3:
    if cmd_size==4:
      print '  writel('+str(cmd_val)+','+str(cmd_addr)+'+'+pbase[0]+');'
    else:
      print '  writeb('+str(cmd_val)+','+str(cmd_addr)+'+'+pbase[0]+');'
  elif cmd_type==4:
    if cmd_size==4:
      print '  writel('+str(cmd_val)+','+str(cmd_addr)+'+'+pbase[1]+');'
    else:
      print '  writeb('+str(cmd_val)+','+str(cmd_addr)+'+'+pbase[1]+');'
  elif cmd_type==5:
    if cmd_size==4:
      print '  writel('+str(cmd_val)+','+str(cmd_addr)+'+'+pbase[2]+');'
    else:
      print '  writeb('+str(cmd_val)+','+str(cmd_addr)+'+'+pbase[2]+');'
  elif cmd_type==6:
    print '  writel('+str(cmd_val)+','+str(cmd_addr)+'+'+pbase[0]+');'

