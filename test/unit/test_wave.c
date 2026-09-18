/*  test_wave.c - unit tests for WAVE header construction helpers
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

#include <string.h>
#include "unity.h"
#include "shntool.h"

void setUp(void) {}

void tearDown(void) {}

static void test_format_to_str_known(void) {
  TEST_ASSERT_EQUAL_STRING("Microsoft PCM", format_to_str(WAVE_FORMAT_PCM));
  TEST_ASSERT_EQUAL_STRING("Microsoft ADPCM", format_to_str(WAVE_FORMAT_ADPCM));
}

static void test_format_to_str_unknown(void) {
  TEST_ASSERT_EQUAL_STRING("Unknown", format_to_str(0x7fff));
}

static void test_make_canonical_header(void) {
  unsigned char header[CANONICAL_HEADER_SIZE];
  wave_info info;

  memset(&info, 0, sizeof(info));
  info.chunk_size = 1036;
  info.wave_format = WAVE_FORMAT_PCM;
  info.channels = 2;
  info.samples_per_sec = 44100;
  info.avg_bytes_per_sec = 176400;
  info.block_align = 4;
  info.bits_per_sample = 16;
  info.data_size = 1000;

  make_canonical_header(header, &info);

  TEST_ASSERT_EQUAL_MEMORY("RIFF", header, 4);
  TEST_ASSERT_EQUAL_MEMORY("WAVE", header + 8, 4);
  TEST_ASSERT_EQUAL_MEMORY("fmt ", header + 12, 4);
  TEST_ASSERT_EQUAL_MEMORY("data", header + 36, 4);
  TEST_ASSERT_EQUAL_UINT32(1036u, (UNITY_UINT32)uchar_to_ulong_le(header + 4));
  TEST_ASSERT_EQUAL_UINT16(1u, (UNITY_UINT16)uchar_to_ushort_le(header + 20));
  TEST_ASSERT_EQUAL_UINT16(2u, (UNITY_UINT16)uchar_to_ushort_le(header + 22));
  TEST_ASSERT_EQUAL_UINT32(44100u,
                           (UNITY_UINT32)uchar_to_ulong_le(header + 24));
  TEST_ASSERT_EQUAL_UINT32(1000u, (UNITY_UINT32)uchar_to_ulong_le(header + 40));
}

static void test_make_canonical_header_null(void) {
  make_canonical_header(NULL, NULL);
}

static void test_put_chunk_size(void) {
  unsigned char header[CANONICAL_HEADER_SIZE];

  memset(header, 0, sizeof(header));
  put_chunk_size(header, 0x12345678ul);
  TEST_ASSERT_EQUAL_UINT32(0x12345678u,
                           (UNITY_UINT32)uchar_to_ulong_le(header + 4));
}

static void test_put_data_size(void) {
  unsigned char header[CANONICAL_HEADER_SIZE];

  memset(header, 0, sizeof(header));
  put_data_size(header, CANONICAL_HEADER_SIZE, 1000);
  TEST_ASSERT_EQUAL_UINT32(1000u, (UNITY_UINT32)uchar_to_ulong_le(header + 40));
  TEST_ASSERT_EQUAL_UINT32(1036u, (UNITY_UINT32)uchar_to_ulong_le(header + 4));
}

int main(void) {
  UNITY_BEGIN();

  RUN_TEST(test_format_to_str_known);
  RUN_TEST(test_format_to_str_unknown);
  RUN_TEST(test_make_canonical_header);
  RUN_TEST(test_make_canonical_header_null);
  RUN_TEST(test_put_chunk_size);
  RUN_TEST(test_put_data_size);

  return UNITY_END();
}
