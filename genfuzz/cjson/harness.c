#include "cJSON/cJSON.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* 파일 하나를 읽어 JSON으로 파싱하고, 출력(직렬화)·복제·검색·삭제까지 해 본다. */
int main(int argc,char**argv){
  if(argc<2) return 1;
  FILE*f=fopen(argv[1],"rb"); if(!f) return 1;
  fseek(f,0,SEEK_END); long n=ftell(f); fseek(f,0,SEEK_SET);
  if(n<0||n>1000000){fclose(f);return 1;}
  char*buf=malloc(n+1); if(!buf){fclose(f);return 1;}
  size_t r=fread(buf,1,n,f); fclose(f); buf[r]=0;
  cJSON*j=cJSON_Parse(buf);
  if(j){
    char*s=cJSON_Print(j); if(s) free(s);
    s=cJSON_PrintUnformatted(j); if(s) free(s);
    cJSON*c=cJSON_Duplicate(j,1); if(c){ cJSON_Compare(j,c,1); cJSON_Delete(c);}
    cJSON_GetObjectItem(j,"a"); cJSON_GetArraySize(j);
    cJSON_Delete(j);
    cJSON_Minify(buf);   /* 파싱에 성공한 입력만 Minify 한다(Minify 단독 호출은 얕은 입력에서 바로 죽어 단계 비교가 무의미해진다) */
  }
  free(buf); return 0;}
