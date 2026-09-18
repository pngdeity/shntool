/*  test_module.c - unit tests for the shared module helpers
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

#include <stdlib.h>
#include "unity.h"
#include "shntool.h"

void setUp(void) {}

void tearDown(void) {}

static void test_trim_newline(void) {
  char buf[] = "hello\n";

  trim(buf);
  TEST_ASSERT_EQUAL_STRING("hello", buf);
}

static void test_trim_crlf(void) {
  char buf[] = "hello\r\n";

  trim(buf);
  TEST_ASSERT_EQUAL_STRING("hello", buf);
}

static void test_trim_multiple(void) {
  char buf[] = "hello\n\r\n";

  trim(buf);
  TEST_ASSERT_EQUAL_STRING("hello", buf);
}

static void test_trim_noop(void) {
  char buf[] = "hello";

  trim(buf);
  TEST_ASSERT_EQUAL_STRING("hello", buf);
}

static void test_trim_all_newlines(void) {
  char buf[] = "\n\r\n";

  trim(buf);
  TEST_ASSERT_EQUAL_STRING("", buf);
}

static void test_basename_with_directory(void) {
  char path[] = "/some/dir/file.wav";

  TEST_ASSERT_EQUAL_STRING("file.wav", basename(path));
}

static void test_basename_without_directory(void) {
  char path[] = "file.wav";

  TEST_ASSERT_EQUAL_STRING("file.wav", basename(path));
}

static void test_extname_present(void) {
  char path[] = "/some/dir/file.wav";

  TEST_ASSERT_EQUAL_STRING("wav", extname(path));
}

static void test_extname_absent(void) {
  char path[] = "/some/dir/file";

  TEST_ASSERT_NULL(extname(path));
}

static void test_extname_dot_in_directory(void) {
  char path[] = "/some.d/file";

  TEST_ASSERT_NULL(extname(path));
}

static void test_scan_env_present(void) {
  setenv("ST_UNIT_TEST_SCAN", "value", 1);
  TEST_ASSERT_EQUAL_STRING("value", scan_env("ST_UNIT_TEST_SCAN"));
  unsetenv("ST_UNIT_TEST_SCAN");
}

static void test_scan_env_empty_is_null(void) {
  setenv("ST_UNIT_TEST_SCAN", "", 1);
  TEST_ASSERT_NULL(scan_env("ST_UNIT_TEST_SCAN"));
  unsetenv("ST_UNIT_TEST_SCAN");
}

static void test_scan_env_unset_is_null(void) {
  unsetenv("ST_UNIT_TEST_SCAN");
  TEST_ASSERT_NULL(scan_env("ST_UNIT_TEST_SCAN"));
}

int main(void) {
  UNITY_BEGIN();

  RUN_TEST(test_trim_newline);
  RUN_TEST(test_trim_crlf);
  RUN_TEST(test_trim_multiple);
  RUN_TEST(test_trim_noop);
  RUN_TEST(test_trim_all_newlines);
  RUN_TEST(test_basename_with_directory);
  RUN_TEST(test_basename_without_directory);
  RUN_TEST(test_extname_present);
  RUN_TEST(test_extname_absent);
  RUN_TEST(test_extname_dot_in_directory);
  RUN_TEST(test_scan_env_present);
  RUN_TEST(test_scan_env_empty_is_null);
  RUN_TEST(test_scan_env_unset_is_null);

  return UNITY_END();
}
