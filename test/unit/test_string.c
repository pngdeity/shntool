/*  test_string.c - unit tests for the bounded string helpers
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
#include "shntool.h"

void setUp(void) {}

void tearDown(void) {}

static void test_strlcpy_fits(void) {
  char buf[8];

  TEST_ASSERT_EQUAL_UINT(2u, (unsigned)st_strlcpy(buf, "hi", sizeof(buf)));
  TEST_ASSERT_EQUAL_STRING("hi", buf);
}

static void test_strlcpy_truncates(void) {
  char buf[8];

  TEST_ASSERT_EQUAL_UINT(10u,
                         (unsigned)st_strlcpy(buf, "abcdefghij", sizeof(buf)));
  TEST_ASSERT_EQUAL_STRING("abcdefg", buf);
}

static void test_strlcpy_zero_size(void) {
  char buf[1] = {'x'};

  TEST_ASSERT_EQUAL_UINT(2u, (unsigned)st_strlcpy(buf, "hi", 0));
  TEST_ASSERT_EQUAL_CHAR('x', buf[0]);
}

static void test_strlcpy_empty_source(void) {
  char buf[8] = "stale";

  TEST_ASSERT_EQUAL_UINT(0u, (unsigned)st_strlcpy(buf, "", sizeof(buf)));
  TEST_ASSERT_EQUAL_STRING("", buf);
}

static void test_strlcat_appends(void) {
  char buf[8] = "abc";

  TEST_ASSERT_EQUAL_UINT(5u, (unsigned)st_strlcat(buf, "de", sizeof(buf)));
  TEST_ASSERT_EQUAL_STRING("abcde", buf);
}

static void test_strlcat_truncates(void) {
  char buf[8] = "abc";

  TEST_ASSERT_EQUAL_UINT(7u, (unsigned)st_strlcat(buf, "defg", sizeof(buf)));
  TEST_ASSERT_EQUAL_STRING("abcdefg", buf);
}

static void test_strlcat_reports_full_length(void) {
  char buf[8] = "abc";

  TEST_ASSERT_EQUAL_UINT(10u,
                         (unsigned)st_strlcat(buf, "defghij", sizeof(buf)));
  TEST_ASSERT_EQUAL_STRING("abcdefg", buf);
}

static void test_strlcat_on_unterminated_buffer(void) {
  char buf[4];
  size_t n;

  buf[0] = 'a';
  buf[1] = 'b';
  buf[2] = 'c';
  buf[3] = 'd';

  n = st_strlcat(buf, "x", sizeof(buf));
  TEST_ASSERT_EQUAL_UINT(5u, (unsigned)n);
  TEST_ASSERT_EQUAL_MEMORY("abcd", buf, sizeof(buf));
}

static void test_snprintf_terminates(void) {
  char buf[5];

  st_snprintf(buf, sizeof(buf), "%s", "abcdefg");
  TEST_ASSERT_EQUAL_STRING("abcd", buf);
}

static void test_snprintf_exact_fit(void) {
  char buf[5];

  st_snprintf(buf, sizeof(buf), "%s", "abcd");
  TEST_ASSERT_EQUAL_STRING("abcd", buf);
}

int main(void) {
  UNITY_BEGIN();

  RUN_TEST(test_strlcpy_fits);
  RUN_TEST(test_strlcpy_truncates);
  RUN_TEST(test_strlcpy_zero_size);
  RUN_TEST(test_strlcpy_empty_source);
  RUN_TEST(test_strlcat_appends);
  RUN_TEST(test_strlcat_truncates);
  RUN_TEST(test_strlcat_reports_full_length);
  RUN_TEST(test_strlcat_on_unterminated_buffer);
  RUN_TEST(test_snprintf_terminates);
  RUN_TEST(test_snprintf_exact_fit);

  return UNITY_END();
}
