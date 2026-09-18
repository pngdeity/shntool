/*  fuzz_cue.c - libFuzzer entry point for the CUE-sheet tokenizer
 *  Copyright (C) 2000-2009  Jason Jordan <shnutils@freeshell.org>
 *
 *  This program is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU General Public License
 *  as published by the Free Software Foundation; either version 2
 *  of the License, or (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
 * USA.
 */

/*
 * Splits the input into lines and feeds each one to the CUE tokenizer used by
 * shnsplit, exercising keyword extraction, field parsing and the raw
 * split-point length extractor. The hooks are compiled into shntool_core only
 * when ST_FUZZ is defined (i.e. in a -Dfuzz=true build).
 */

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "shntool.h"

void st_cue_parse_begin(void);
void st_cue_parse_line(unsigned char *line);

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  unsigned char *buf;
  size_t i, start;

  if (size == 0 || size > (1u << 20))
    return 0;

  buf = malloc(size + 1);
  if (NULL == buf)
    return 0;
  memcpy(buf, data, size);
  buf[size] = 0;

  st_cue_parse_begin();

  start = 0;
  for (i = 0; i <= size; i++) {
    if ((i == size) || (buf[i] == '\n') || (buf[i] == '\0')) {
      unsigned char saved = buf[i];

      buf[i] = 0;
      st_cue_parse_line(buf + start);

      if (i == size)
        break;

      buf[i] = saved;
      start = i + 1;
    }
  }

  free(buf);

  return 0;
}
