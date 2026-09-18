/*  fuzz_id3v2.c - libFuzzer entry point for the ID3v2 tag detector
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
 * Feeds arbitrary bytes to check_for_id3v2_tag() through an in-memory FILE
 * stream, exercising the ID3v2 header validation and synchsafe size parsing.
 *
 * Build with -Dfuzz=true in a dedicated build directory.
 */

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include "shntool.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  FILE *stream;

  if (size == 0)
    return 0;

  stream = fmemopen((void *)data, size, "rb");
  if (NULL == stream)
    return 0;

  (void)check_for_id3v2_tag(stream);

  fclose(stream);

  return 0;
}
