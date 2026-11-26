#include <yaml.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* 파일을 YAML로 파싱해 이벤트를 끝까지 읽고, 같은 이벤트를 다시 YAML로 내보내고(emitter), 문서 단위로도 읽는다(loader). */
static int wr(void*d, unsigned char*b, size_t n){ (void)d;(void)b;(void)n; return 1; }
int main(int argc,char**argv){
  if(argc<2) return 1;
  FILE*f=fopen(argv[1],"rb"); if(!f) return 1;
  yaml_parser_t p; yaml_event_t ev; yaml_emitter_t em; int emit_ok;
  yaml_parser_initialize(&p); yaml_parser_set_input_file(&p,f);
  emit_ok = yaml_emitter_initialize(&em); if(emit_ok){ yaml_emitter_set_output(&em,wr,NULL); }
  int n=0;
  while(n++<20000){
    if(!yaml_parser_parse(&p,&ev)) break;
    int end = (ev.type==YAML_STREAM_END_EVENT);
    if(emit_ok){ if(!yaml_emitter_emit(&em,&ev)) emit_ok=0; } else yaml_event_delete(&ev);
    if(end) break;
  }
  yaml_parser_delete(&p); if(emit_ok||1) yaml_emitter_delete(&em);
  fclose(f);
  /* 문서 로더 */
  f=fopen(argv[1],"rb"); if(!f) return 0;
  yaml_parser_t p2; yaml_document_t doc;
  yaml_parser_initialize(&p2); yaml_parser_set_input_file(&p2,f);
  for(int i=0;i<64;i++){ if(!yaml_parser_load(&p2,&doc)) break; int e=!yaml_document_get_root_node(&doc); yaml_document_delete(&doc); if(e) break; }
  yaml_parser_delete(&p2); fclose(f);
  return 0;}
