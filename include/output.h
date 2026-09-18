/*  output.h - output functions
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
 * $Id: output.h,v 1.11 2009/03/11 17:18:01 jason Exp $
 */

#ifndef __OUTPUT_H__
#define __OUTPUT_H__

#if defined(__GNUC__) || defined(__clang__)
#define ST_PRINTF_FORMAT(fmt_idx, first_arg)                                   \
  __attribute__((format(printf, fmt_idx, first_arg)))
#else
#define ST_PRINTF_FORMAT(fmt_idx, first_arg)
#endif

#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
#define ST_NORETURN _Noreturn
#elif defined(__GNUC__) || defined(__clang__)
#define ST_NORETURN __attribute__((noreturn))
#else
#define ST_NORETURN
#endif

void st_output(char *, ...) ST_PRINTF_FORMAT(1, 2);
void st_info(char *, ...) ST_PRINTF_FORMAT(1, 2);
void st_warning(char *, ...) ST_PRINTF_FORMAT(1, 2);
ST_NORETURN void st_error(char *, ...) ST_PRINTF_FORMAT(1, 2);
ST_NORETURN void st_help(char *, ...) ST_PRINTF_FORMAT(1, 2);
void st_debug1(char *, ...) ST_PRINTF_FORMAT(1, 2);
void st_debug2(char *, ...) ST_PRINTF_FORMAT(1, 2);
void st_debug3(char *, ...) ST_PRINTF_FORMAT(1, 2);

#endif
