/*  test_convert.c - unit tests for the endian conversion helpers
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

#include "unity.h"
#include "convert.h"

void setUp(void) {}

void tearDown(void) {}

static void test_little_endian_uint32(void) {
  unsigned char buf[4] = {0x78, 0x56, 0x34, 0x12};

  TEST_ASSERT_EQUAL_UINT32(0x12345678u, (UNITY_UINT32)uchar_to_ulong_le(buf));
}

static void test_little_endian_uint16(void) {
  unsigned char buf[2] = {0x34, 0x12};

  TEST_ASSERT_EQUAL_UINT16(0x1234u, (UNITY_UINT16)uchar_to_ushort_le(buf));
}

static void test_big_endian_uint32(void) {
  unsigned char buf[4] = {0x12, 0x34, 0x56, 0x78};

  TEST_ASSERT_EQUAL_UINT32(0x12345678u, (UNITY_UINT32)uchar_to_ulong_be(buf));
}

static void test_big_endian_uint16(void) {
  unsigned char buf[2] = {0x12, 0x34};

  TEST_ASSERT_EQUAL_UINT16(0x1234u, (UNITY_UINT16)uchar_to_ushort_be(buf));
}

static void test_ulong_le_round_trip(void) {
  unsigned char buf[4];

  ulong_to_uchar_le(buf, 0xDEADBEEFul);
  TEST_ASSERT_EQUAL_UINT32(0xDEADBEEFu, (UNITY_UINT32)uchar_to_ulong_le(buf));
}

static void test_ulong_be_round_trip(void) {
  unsigned char buf[4];

  ulong_to_uchar_be(buf, 0x01020304ul);
  TEST_ASSERT_EQUAL_UINT8(0x01u, buf[0]);
  TEST_ASSERT_EQUAL_UINT8(0x04u, buf[3]);
  TEST_ASSERT_EQUAL_UINT32(0x01020304u, (UNITY_UINT32)uchar_to_ulong_be(buf));
}

static void test_ushort_le_round_trip(void) {
  unsigned char buf[2];

  ushort_to_uchar_le(buf, 0xBEEFu);
  TEST_ASSERT_EQUAL_UINT8(0xEFu, buf[0]);
  TEST_ASSERT_EQUAL_UINT8(0xBEu, buf[1]);
  TEST_ASSERT_EQUAL_UINT16(0xBEEFu, (UNITY_UINT16)uchar_to_ushort_le(buf));
}

static void test_ushort_be_round_trip(void) {
  unsigned char buf[2];

  ushort_to_uchar_be(buf, 0xBEEFu);
  TEST_ASSERT_EQUAL_UINT8(0xBEu, buf[0]);
  TEST_ASSERT_EQUAL_UINT8(0xEFu, buf[1]);
  TEST_ASSERT_EQUAL_UINT16(0xBEEFu, (UNITY_UINT16)uchar_to_ushort_be(buf));
}

static void test_synchsafe_int(void) {
  /* 0x00 0x00 0x01 0x00 -> 0x80 (all high bits must be ignored) */
  unsigned char buf[4] = {0x80, 0x80, 0x81, 0x80};

  TEST_ASSERT_EQUAL_UINT32(128u, (UNITY_UINT32)synchsafe_int_to_ulong(buf));
}

int main(void) {
  UNITY_BEGIN();

  RUN_TEST(test_little_endian_uint32);
  RUN_TEST(test_little_endian_uint16);
  RUN_TEST(test_big_endian_uint32);
  RUN_TEST(test_big_endian_uint16);
  RUN_TEST(test_ulong_le_round_trip);
  RUN_TEST(test_ulong_be_round_trip);
  RUN_TEST(test_ushort_le_round_trip);
  RUN_TEST(test_ushort_be_round_trip);
  RUN_TEST(test_synchsafe_int);

  return UNITY_END();
}
