project('shntool', 'c',
  version: '3.0.10',
  license: 'GPL-2.0-or-later',
  meson_version: '>=1.1.0',
  default_options: [
    'c_std=gnu17',
    'warning_level=2',
    'werror=true',
    'buildtype=debugoptimized',
    'b_ndebug=if-release',
  ],
)

cc = meson.get_compiler('c')
python = import('python').find_installation()

# --- Generated configuration header -----------------------------------------

conf = configuration_data()
conf.set_quoted('PACKAGE', meson.project_name())
conf.set_quoted('PACKAGE_NAME', meson.project_name())
conf.set_quoted('PACKAGE_TARNAME', meson.project_name())
conf.set_quoted('PACKAGE_STRING', meson.project_name() + ' ' + meson.project_version())
conf.set_quoted('PACKAGE_VERSION', meson.project_version())
conf.set_quoted('VERSION', meson.project_version())
conf.set_quoted('PACKAGE_BUGREPORT', 'shnutils@freeshell.org')

foreach header : ['inttypes.h', 'memory.h', 'stdint.h', 'stdlib.h', 'string.h',
                  'strings.h', 'sys/stat.h', 'sys/types.h', 'unistd.h']
  if cc.has_header(header)
    conf.set('HAVE_' + header.underscorify().to_upper(), 1)
  endif
endforeach

foreach func : ['atol', 'strerror', 'sysconf']
  if cc.has_function(func)
    conf.set('HAVE_' + func.to_upper(), 1)
  endif
endforeach

if host_machine.endian() == 'big'
  conf.set('WORDS_BIGENDIAN', 1)
endif

if host_machine.system() == 'windows'
  conf.set('HAVE_WINDOWS_H', 1)
  conf.set('WIN32', 1)
endif

config_h = configure_file(output: 'config.h', configuration: conf)

# --- Compiler options --------------------------------------------------------

project_args = ['-DHAVE_CONFIG_H']

# The trailing child_args slots of the mode/format structs are filled in at
# runtime and are intentionally omitted from module initializers.
project_args += cc.get_supported_arguments(['-Wno-missing-field-initializers'])

fuzz_enabled = get_option('fuzz')

if get_option('hardening')
  project_args += cc.get_supported_arguments([
    '-fstack-protector-strong',
    '-fstack-clash-protection',
    '-fcf-protection',
  ])
  # _FORTIFY_SOURCE conflicts with the sanitizer runtime used by fuzz builds
  if get_option('optimization') != '0' and not fuzz_enabled
    project_args += cc.get_supported_arguments(['-D_FORTIFY_SOURCE=3'])
  endif
  add_project_link_arguments(
    cc.get_supported_link_arguments(['-Wl,-z,relro', '-Wl,-z,now']),
    language: 'c',
  )
endif

if fuzz_enabled
  if cc.get_id() != 'clang'
    error('the fuzz build requires clang, but the C compiler is ' + cc.get_id())
  endif
  # Instrument every object for coverage and memory-safety checks. The
  # libFuzzer runtime (and its main()) is only linked into the fuzz targets.
  project_args += [
    '-fsanitize=fuzzer-no-link,address,undefined',
    '-fno-omit-frame-pointer',
    '-DST_FUZZ',
  ]
  # Every target needs the sanitizer runtime; only the fuzz target links the
  # libFuzzer runtime (and its main()).
  add_project_link_arguments(['-fsanitize=address,undefined'], language: 'c')
endif

add_project_arguments(project_args, language: 'c')

inc = include_directories('include')

# --- Module sources ----------------------------------------------------------

# Everything except the program entry point lives in shntool_core so that unit
# tests and fuzz targets can link against it without pulling in main().
core_sources = files(
  'src/core_convert.c',
  'src/core_fileio.c',
  'src/core_format.c',
  'src/core_mode.c',
  'src/core_module.c',
  'src/core_output.c',
  'src/core_wave.c',
)

mode_files = {
  'cat':   files('src/mode_cat.c'),
  'cmp':   files('src/mode_cmp.c'),
  'conv':  files('src/mode_conv.c'),
  'cue':   files('src/mode_cue.c'),
  'fix':   files('src/mode_fix.c'),
  'gen':   files('src/mode_gen.c'),
  'hash':  files('src/mode_hash.c'),
  'info':  files('src/mode_info.c'),
  'join':  files('src/mode_join.c'),
  'len':   files('src/mode_len.c'),
  'pad':   files('src/mode_pad.c'),
  'split': files('src/mode_split.c'),
  'strip': files('src/mode_strip.c'),
  'trim':  files('src/mode_trim.c'),
}

format_files = {
  'aiff': files('src/format_aiff.c'),
  'alac': files('src/format_alac.c'),
  'als':  files('src/format_als.c'),
  'ape':  files('src/format_ape.c'),
  'bonk': files('src/format_bonk.c'),
  'cust': files('src/format_cust.c'),
  'flac': files('src/format_flac.c'),
  'kxs':  files('src/format_kxs.c'),
  'la':   files('src/format_la.c'),
  'lpac': files('src/format_lpac.c'),
  'mkw':  files('src/format_mkw.c'),
  'null': files('src/format_null.c'),
  'ofr':  files('src/format_ofr.c'),
  'shn':  files('src/format_shn.c'),
  'tak':  files('src/format_tak.c'),
  'term': files('src/format_term.c'),
  'tta':  files('src/format_tta.c'),
  'wav':  files('src/format_wav.c'),
  'wv':   files('src/format_wv.c'),
}

enabled_modes = []
foreach name : get_option('modes').split(',')
  name = name.strip()
  if name == ''
    continue
  elif not mode_files.has_key(name)
    warning('unknown mode module: ' + name)
  else
    enabled_modes += name
  endif
endforeach

enabled_formats = []
foreach name : get_option('formats').split(',')
  name = name.strip()
  if name == ''
    continue
  elif not format_files.has_key(name)
    warning('unknown format module: ' + name)
  else
    enabled_formats += name
  endif
endforeach

if enabled_modes.length() == 0
  error('at least one mode module must be enabled')
endif
if enabled_formats.length() == 0
  error('at least one format module must be enabled')
endif

glue_modes = custom_target('glue_modes',
  output: 'glue_modes.c',
  command: [python, files('utils/gen_glue.py'), 'mode', '@OUTPUT@'] + enabled_modes,
)

glue_formats = custom_target('glue_formats',
  output: 'glue_formats.c',
  command: [python, files('utils/gen_glue.py'), 'format', '@OUTPUT@'] + enabled_formats,
)

mode_sources = []
foreach name : enabled_modes
  mode_sources += mode_files[name]
endforeach

format_sources = []
foreach name : enabled_formats
  format_sources += format_files[name]
endforeach

# --- Targets -----------------------------------------------------------------

shntool_core = static_library('shntool_core',
  core_sources,
  glue_modes,
  glue_formats,
  mode_sources,
  format_sources,
  config_h,
  include_directories: inc,
)

shntool = executable('shntool',
  'src/core_shntool.c',
  config_h,
  link_with: shntool_core,
  include_directories: inc,
  install: true,
)

install_man('man/shntool.1')

foreach name : enabled_modes
  install_symlink('shn' + name,
    pointing_to: 'shntool',
    install_dir: get_option('bindir'),
  )
endforeach

# --- Tests -------------------------------------------------------------------

# The sanitized test runs check memory safety and leaks: overflows,
# use-after-free and undefined behaviour abort immediately, and lost
# allocations are reported.
test_env = {}
if fuzz_enabled
  test_env += {'ASAN_OPTIONS': 'detect_leaks=1:halt_on_error=1:abort_on_error=1'}
  test_env += {'UBSAN_OPTIONS': 'halt_on_error=1:abort_on_error=1:print_stacktrace=1'}
endif

test('smoke', python,
  args: [files('test/smoke.py'), '--binary', shntool.full_path()],
  env: test_env,
  timeout: 120,
)

reference_shntool = get_option('reference-shntool')
if reference_shntool != ''
  test('differential', python,
    args: [
      files('test/differential.py'),
      '--candidate', shntool.full_path(),
      '--reference', reference_shntool,
    ],
    env: test_env,
    timeout: 600,
  )
endif

# --- Unit tests --------------------------------------------------------------

unity_dep = dependency('unity', fallback: ['unity', 'unity_dep'])

unit_test_names = ['convert', 'module', 'string', 'mode', 'wave']

foreach name : unit_test_names
  unit_test = executable('test_' + name,
    files('test/unit/test_' + name + '.c'),
    'test/unit/support.c',
    config_h,
    link_with: shntool_core,
    include_directories: inc,
    dependencies: unity_dep,
  )
  test('unit-' + name, unit_test, env: test_env, timeout: 60)
endforeach

# --- Fuzzing -----------------------------------------------------------------

if fuzz_enabled
  # Each fuzz target links the test support object (st_priv/st_input/st_version)
  # rather than core_shntool.c, so no main() is pulled in.
  fuzz_targets = {
    'fuzz_wave': {'max_len': 4096},
    'fuzz_id3v2': {'max_len': 512},
    'fuzz_cue': {'max_len': 16384},
  }

  foreach name, opts : fuzz_targets
    fuzz_exe = executable(name,
      'test/fuzz/' + name + '.c',
      'test/unit/support.c',
      config_h,
      link_args: ['-fsanitize=fuzzer,address,undefined'],
      link_with: shntool_core,
      include_directories: inc,
    )

    test(name,
      python,
      args: [
        files('test/fuzz/run_fuzz.py'),
        '--fuzzer', fuzz_exe.full_path(),
        '--max-len', opts['max_len'].to_string(),
      ],
      env: test_env,
      timeout: 600,
    )
  endforeach
endif
