/*  support.c - globals normally provided by core_shntool.c
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
 * The unit tests link against shntool_core, which deliberately excludes
 * core_shntool.c (it defines main()). These two globals live there, so the
 * test binaries provide their own zero-initialised copies.
 */

#include "shntool.h"

private_opts st_priv;
input_files st_input;

/* core_mode.c's st_getopt() calls this on -v; the real one lives in
   core_shntool.c, which is excluded from shntool_core. */
void st_version(void) {}
