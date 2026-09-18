/*  fuzz_wave.c - libFuzzer entry point for the WAVE header parser
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
 * Feeds arbitrary bytes to verify_wav_header_internal() through an in-memory
 * FILE stream. This exercises the RIFF/fmt/data chunk walker, the header
 * consistency checks and the length formatting logic without touching disk.
 *
 * Build with -Dfuzz=true in a dedicated build directory:
 *   meson setup build-fuzz -Dfuzz=true
 *   meson test -C build-fuzz fuzz-smoke
 */

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "shntool.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  wave_info *info;
  FILE *stream;

  if (size == 0)
    return 0;

  stream = fmemopen((void *)data, size, "rb");
  if (NULL == stream)
    return 0;

  info = calloc(1, sizeof(*info));
  if (NULL == info) {
    fclose(stream);
    return 0;
  }

  info->filename = (char *)"fuzz.wav";
  info->input = stream;
  info->actual_size = (wlong)size;
  info->input_format = NULL;

  verify_wav_header_internal(info, FALSE);

  st_free(info);
  fclose(stream);

  return 0;
}
