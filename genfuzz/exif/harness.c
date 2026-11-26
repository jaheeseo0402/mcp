#include <libexif/exif-data.h>
#include <stdio.h>
#include <stdlib.h>
#ifdef TRIAGE
#include <execinfo.h>
#include <dlfcn.h>
#include <signal.h>
#include <string.h>
#include <unistd.h>
/* crash 위치 기록용: 시그널을 받으면 호출 스택에서 exifbin 안의 앞쪽 3개 위치(함수 이름, 없으면 +오프셋)를 한 줄로 찍는다.
   힙이 깨진 상태에서도 동작하도록 malloc을 쓰지 않는다(backtrace_symbols 대신 dladdr). */
static void on_sig(int s){
  void *b[16]; int n = backtrace(b,16);
  char out[512]; int k=0, m=0; k += snprintf(out,sizeof out,"[CRASH sig%d",s);
  for(int i=1;i<n && m<3;i++){ Dl_info di;
    if(!dladdr(b[i],&di) || !di.dli_fname || !strstr(di.dli_fname,"exifbin")) continue;
    if(di.dli_sname) k += snprintf(out+k,sizeof out-k," %s",di.dli_sname);
    else k += snprintf(out+k,sizeof out-k," +0x%lx",(unsigned long)((char*)b[i]-(char*)di.dli_fbase));
    m++; }
  snprintf(out+k,sizeof out-k,"]\n"); if(write(2,out,strlen(out))<0) {} _exit(100+s);
}
#endif
int main(int argc,char**argv){
#ifdef TRIAGE
  { void *warm[2]; backtrace(warm,2); /* backtrace 첫 호출은 내부에서 메모리를 쓰므로 미리 한 번 호출해 둔다 */
    /* 스택이 바닥난 crash도 잡도록 비상 스택(sigaltstack) 위에서 처리 함수를 실행한다 */
    static char altstk[65536]; stack_t ss = { .ss_sp = altstk, .ss_size = sizeof altstk, .ss_flags = 0 };
    sigaltstack(&ss, NULL);
    struct sigaction sa; memset(&sa, 0, sizeof sa); sa.sa_handler = on_sig; sa.sa_flags = SA_ONSTACK; sigemptyset(&sa.sa_mask);
    sigaction(SIGSEGV,&sa,NULL); sigaction(SIGABRT,&sa,NULL); sigaction(SIGBUS,&sa,NULL); sigaction(SIGFPE,&sa,NULL); }
#endif
  if(argc<2) return 1;
  ExifData *d = exif_data_new_from_file(argv[1]);
  if(d){ char buf[1024]; for(int i=0;i<EXIF_IFD_COUNT;i++){ ExifContent*c=d->ifd[i]; if(!c) continue;
     for(unsigned j=0;j<c->count;j++){ exif_entry_get_value(c->entries[j],buf,sizeof buf);} }
     unsigned char *o; unsigned int l; exif_data_save_data(d,&o,&l); free(o); exif_data_unref(d);}
  return 0;}
