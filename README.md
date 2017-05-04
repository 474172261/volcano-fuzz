# volcano-fuzz
a fuzz framework for fuzzing qemu.
1. use add_file_checkpoint.py to add checkpoint to modules which you want to fuzz.
2. make vfuzz.c to vfuzz.ko in Guest system,and insmod it
3. run vfuzz-server.py in Host System.
4. then run vfuzz-client.py in Guest System.

from now on,I just support the vmw_pvscsi.c module for fuzzing,you can add your fuzz script to this,and make a little change.
