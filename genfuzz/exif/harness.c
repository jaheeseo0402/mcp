#include <libexif/exif-data.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char**argv){
  if(argc<2) return 1;
  ExifData *d = exif_data_new_from_file(argv[1]);
  if(d){ char buf[1024]; for(int i=0;i<EXIF_IFD_COUNT;i++){ ExifContent*c=d->ifd[i]; if(!c) continue;
     for(unsigned j=0;j<c->count;j++){ exif_entry_get_value(c->entries[j],buf,sizeof buf);} }
     unsigned char *o; unsigned int l; exif_data_save_data(d,&o,&l); free(o); exif_data_unref(d);}
  return 0;}
