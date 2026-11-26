#include "lodepng/lodepng.h"
#include <vector>
#include <cstdio>
#include <cstdlib>
/* 파일을 PNG로 읽어 해독(decode)하고, 정보(inspect)와 다시 인코딩까지 해 본다.
   퍼징에서 CRC·adler32 검사에 막히지 않도록 해독기가 이를 무시하게 설정했다(libpng 퍼징 하네스에서도 흔한 설정). */
int main(int argc,char**argv){
  if(argc<2) return 1;
  FILE*f=fopen(argv[1],"rb"); if(!f) return 1;
  std::vector<unsigned char> in; unsigned char buf[4096]; size_t r;
  while((r=fread(buf,1,sizeof buf,f))>0){ in.insert(in.end(),buf,buf+r); if(in.size()>1000000) break; }
  fclose(f);
  lodepng::State st;
  st.decoder.ignore_crc=1; st.decoder.zlibsettings.ignore_adler32=1;
  st.decoder.remember_unknown_chunks=1; st.decoder.read_text_chunks=1;
  unsigned w=0,h=0; std::vector<unsigned char> img;
  unsigned err=lodepng::decode(img,w,h,st,in);
  if(!err && w*(size_t)h<4000000){
    std::vector<unsigned char> out; lodepng::State es; es.info_raw=st.info_raw; es.info_png.color=st.info_png.color;
    lodepng::encode(out,img,w,h,es);
  }
  return 0;}
