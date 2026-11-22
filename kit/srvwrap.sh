#!/bin/bash
exec node --require "$KIT/covpre2.cjs" "$SERVER_ENTRY_REAL" "$@"
