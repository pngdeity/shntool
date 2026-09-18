/*  test_mode.c - unit tests for split-point parsing and length formatting
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

static void init_info(wave_info *info, unsigned long problems, wlong rate) {
  memset(info, 0, sizeof(*info));
  info->problems = problems;
  info->rate = rate;
}

static void test_smrt_parse_plain_bytes(void) {
  wave_info info;

  init_info(&info, PROBLEM_NOT_CD_QUALITY, 1000);
  TEST_ASSERT_EQUAL_UINT(1500u,
                         (unsigned)smrt_parse((unsigned char *)"1500", &info));
}

static void test_smrt_parse_m_ss(void) {
  wave_info info;

  init_info(&info, PROBLEM_NOT_CD_QUALITY, 1000);
  TEST_ASSERT_EQUAL_UINT(90000u,
                         (unsigned)smrt_parse((unsigned char *)"1:30", &info));
}

static void test_smrt_parse_m_ss_nnn(void) {
  wave_info info;

  init_info(&info, PROBLEM_NOT_CD_QUALITY, 1000);
  TEST_ASSERT_EQUAL_UINT(
      1500u, (unsigned)smrt_parse((unsigned char *)"0:01.500", &info));
}

static void test_smrt_parse_m_ss_ff_cd(void) {
  wave_info info;

  init_info(&info, 0, CD_RATE);
  TEST_ASSERT_EQUAL_UINT(
      246960u, (unsigned)smrt_parse((unsigned char *)"0:01.30", &info));
}

static void test_length_to_str_non_cd(void) {
  wave_info info;

  init_info(&info, PROBLEM_NOT_CD_QUALITY, 176400);
  info.exact_length = 65.5;
  st_priv.show_hmmss = FALSE;
  length_to_str(&info);
  TEST_ASSERT_EQUAL_STRING("1:05.500", info.m_ss);
}

static void test_length_to_str_cd(void) {
  wave_info info;

  init_info(&info, 0, CD_RATE);
  info.length = 1;
  info.data_size = CD_RATE;
  st_priv.show_hmmss = FALSE;
  length_to_str(&info);
  TEST_ASSERT_EQUAL_STRING("0:01.00", info.m_ss);
}

static void test_length_to_str_h_mm_ss(void) {
  wave_info info;

  init_info(&info, PROBLEM_NOT_CD_QUALITY, 176400);
  info.exact_length = 3661.0;
  st_priv.show_hmmss = TRUE;
  length_to_str(&info);
  TEST_ASSERT_EQUAL_STRING("1:01:01.000", info.m_ss);
  st_priv.show_hmmss = FALSE;
}

int main(void) {
  UNITY_BEGIN();

  RUN_TEST(test_smrt_parse_plain_bytes);
  RUN_TEST(test_smrt_parse_m_ss);
  RUN_TEST(test_smrt_parse_m_ss_nnn);
  RUN_TEST(test_smrt_parse_m_ss_ff_cd);
  RUN_TEST(test_length_to_str_non_cd);
  RUN_TEST(test_length_to_str_cd);
  RUN_TEST(test_length_to_str_h_mm_ss);

  return UNITY_END();
}
