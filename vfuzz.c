#include <linux/module.h>
#include <asm/io.h>
#include <linux/kernel.h>
#include <linux/proc_fs.h>
#include <linux/string.h>
#include <linux/vmalloc.h>
#include <asm/uaccess.h>
#include <linux/slab.h>

#define DEBUG 0
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("vfuzz Kernel Module");
MODULE_AUTHOR("VictorV");

#define GNUC_PACKED __attribute__((packed))
void *mymem=NULL;
#define MEMMAX 0x100000
void * mymalloc(int size){
  static int off=0;
  if(off+size>=MEMMAX){
    off=0;
  }
  if(size>MEMMAX){
    printk("Error: request size is bigger than cache.\n");
    return 0;
  }
  u64 memaddr=(u64)mymem+off;
  memset(memaddr,0,size);
  off+=size;
  return (void *)memaddr;
}

typedef struct {
  u8 type;
  u32 addr;
  u32 senddata;
} GNUC_PACKED ioheader;

#define writeMem(Base) do{\
  if(Base){\
    switch(head->type&0xf0){\
      case 0x10:\
        if(DEBUG)\
          printk("ioMaddr:%p,data:%8x\n",head->addr+Base,head->senddata);\
        else\
          writeb(head->senddata,head->addr+Base);\
        break;\
      case 0x40:\
        if(DEBUG)\
          printk("ioMaddr:%p,data:%8x\n",head->addr+Base,head->senddata);\
        else\
          writel(head->senddata,head->addr+Base);\
        break;\
      default:\
        printk("Error:unhandle Memlen:%x!\n",head->type&0xf0);\
        return -EFAULT;\
    }\
  }\
}while(0)

#define writePort() do{\
  switch(head->type&0xf0){\
    case 0x10:\
      if(DEBUG)\
        printk("iobaddr:%8x,data:%x\n",head->addr,head->senddata);\
      else\
        outb(head->senddata,head->addr);\
      break;\
    case 0x40:\
      if(DEBUG)\
        printk("ioladdr:%8x,data:%8x\n",head->addr,head->senddata);\
      else\
        outl(head->senddata,head->addr);\
      break;\
    default:\
      printk("Error:unhandle Portlen,%x!\n",head->type&0xf0);\
      return -EFAULT;\
  }\
}while(0)

#define writeCopy(Base) do{\
  if(Base){\
    int *mem=(int *)mymalloc(len-5);\
    if(!mem){\
      printk("Error:alloc temp mem fail\n");\
      return -EFAULT;\
    }\
    memcpy(mem,&head->senddata,len-5);\
    if(DEBUG)\
      printk("ioCopy addr:%8x,data:%8x,len:%x\n",head->addr+Base,head->senddata,len-5);\
    else\
      writel(virt_to_phys(mem),head->addr+Base);\
  }\
}while(0)

int times=0;
u64 mapBase[3]={0};
ssize_t writeCallback( struct file *filp,const char __user *buff,unsigned long len,void *data ){
  void *userdata=mymalloc(len);
  if(!userdata){
    printk("Error:alloc cmdcache fail len:%x\n",len);
    return -EFAULT;
  }
  if (copy_from_user(userdata, buff, len )) {
    return -EFAULT;
  }
  int i=0,temp=0;
  if(DEBUG>2){
    printk("in %x:",len);
    for(i=0;i<len;i++){
      printk("%2x ",*((unsigned char *)userdata+i));
    }
    printk("\n");
  }
  times++;
  ioheader *head=(ioheader *)userdata;
  if(DEBUG>1){
    printk("type:%02x,size:%02x\n",head->type&0xf,head->type&0xf0);
    printk("addr:%08x,data:%08x\n",head->addr,head->senddata);
  }
  switch(head->type&0xf){// IOport
    case 0:
      writePort();break;
    case 3:
      writeMem(mapBase[0]);break;
    case 4:
      writeMem(mapBase[1]);break;
    case 5:
      writeMem(mapBase[2]);break;
    case 6:
      writeCopy(mapBase[0]);break;
    case 7:
      writeCopy(mapBase[1]);break;
    case 8:
      writeCopy(mapBase[2]);break;
    case 0xa:// iomap
      temp=(((u8)head->type&0xf0)>>4)-0xa;// 0xa0==base0,0xb0==base1...
      if(temp<0){
        printk("Error:bad num %d.\n",temp);
        return -1;
      }
      mapBase[temp]=(u64)ioremap(head->addr,head->senddata);
      printk("map:0x%8x result:%llx\n",head->addr,mapBase[temp]);
      break;
    case 0xb:
    
    default:
      printk("Error:bad case!\n");
      return -1;
  }
  return len;
}

int readCallback( struct file *filp,char *buf,size_t count,loff_t *offp){
  int len;
  char msg[4];
  *(int *)msg=times;
  copy_to_user(buf,msg,4);
  return 4;
}

static const struct file_operations proc_fops={
  .read =readCallback,
  .write=writeCallback,
  .owner=THIS_MODULE,
};
struct proc_dir_entry *proc_file_entry;

int init_mymodule( void )//初始化
{
  int ret = 0;
  mymem=kmalloc(MEMMAX,GFP_KERNEL);
  if(!mymem){
    printk("mem alloc fail!\n");
    return -ENOMEM;
  }
  proc_file_entry = proc_create("vfuzz",0, NULL, &proc_fops);
  if(proc_file_entry==NULL){
    return -ENOMEM;
  }
  printk("init vfuzz suc!\n");
  return ret;
}

void exit_mymodule( void )
{
  remove_proc_entry("vfuzz",NULL);
  if(mymem)
    kfree(mymem);
  printk(KERN_INFO "vfuzz: Module unloaded.\n");
}
module_init( init_mymodule );
module_exit( exit_mymodule );
