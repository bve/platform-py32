import sys
from os.path import isdir, join
from os import listdir
import re
import difflib

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

FRAMEWORK_DIR = platform.get_package_dir("framework-py32f0sdk")
assert isdir(FRAMEWORK_DIR)

lib_dir = join(FRAMEWORK_DIR, 'libraries')

mcu_long = board.get("build.mcu", "").upper()  # e.g. PY32f003X8
mcu_short = re.findall('PY32F\d\d\d[AB]?', mcu_long)[0]  # PY32F003

if mcu_short == 'PY32F002B':
    dir_prefix = 'PY32F002B'
elif mcu_short.startswith('PY32F07'):
    dir_prefix = 'PY32F07x'
else:
    dir_prefix = 'PY32F0xx'

dir_cmsis = join(FRAMEWORK_DIR, 'CMSIS')

need_hal = '-DUSE_HAL_DRIVER' in env['BUILD_FLAGS']
if need_hal:
    driver_dir = join(FRAMEWORK_DIR, dir_prefix+'_HAL_Driver')
    bsp_dir = join(FRAMEWORK_DIR, dir_prefix+'_HAL_BSP')
else:
    driver_dir = join(FRAMEWORK_DIR, dir_prefix+'_LL_Driver')
    bsp_dir = join(FRAMEWORK_DIR, dir_prefix+'_LL_BSP')


env.Append(
    ASFLAGS=["-x", "assembler-with-cpp"],

    CFLAGS=["-std=gnu17"],

    CCFLAGS=[
        "-Os",  # optimize for size
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
        "-Wall",
        "-mthumb",
        "-nostdlib",
    ],

    CXXFLAGS=[
        "-fno-rtti",
        "-fno-exceptions",
        "-std=gnu++17",
        "-fno-threadsafe-statics"
    ],

    CPPDEFINES=[
        mcu_long,
        mcu_short,
        'PY32F0',
    ],

    # includes
    CPPPATH=[
        join(dir_cmsis, 'Core', 'Include'),
        join(dir_cmsis, 'Device', 'PY32F0xx', 'Include'),
        join(driver_dir, 'Inc'),
        join(bsp_dir, 'Inc'),
        env.subst("${PROJECT_INCLUDE_DIR}"),  # place for py32f0xx_hal_conf.h
    ],

#"-Wl,-Map=${CMAKE_PROJECT_NAME}.map
# -Wl,--gc-sections
# -Wl,--print-memory-usage
# -Wl,--no-warn-rwx-segments
# -T ${CMAKE_SOURCE_DIR}/puya_libs/LDScripts/${PUYA_CHIP}.ld" )
    LINKFLAGS=[
        "-Os",
        "-Wl,--gc-sections",
        "-mthumb",
        "--specs=nano.specs",
        "--specs=nosys.specs",
        "-static",
        "-Wl,--check-sections",
        "-Wl,--unresolved-symbols=report-all",
        "-Wl,--warn-common",
        "-Wl,--warn-section-align",
        "-Wl,--print-memory-usage",
    ],

    LIBSOURCE_DIRS=[join(FRAMEWORK_DIR, 'libraries')],

    LIBS=["c", "m"]
)

env.Append(
    CCFLAGS=[
        "-mcpu=%s" % board.get("build.cpu")
    ],
    LINKFLAGS=[
        "-mcpu=%s" % board.get("build.cpu")
    ]
)

# env.Append(
#     ASFLAGS=[
#         "-mfloat-abi=hard",
#         "-mfpu=fpv4-sp-d16",
#     ],
#     CCFLAGS=[
#         "-mfloat-abi=hard",
#         "-mfpu=fpv4-sp-d16"
#     ],
#     LINKFLAGS=[
#         "-mfloat-abi=hard",
#         "-mfpu=fpv4-sp-d16",
#     ]
# )

env.Append(
    ASFLAGS=env.get("CCFLAGS", [])[:]
)

def parse_num(v:str):
    if v.endswith('K'):
        return int(v[:-1]) * 1024
    elif v.endswith('M'):
        return int(v[:-1]) * 1024 * 1024
    else:
        return int(v, 0)

def get_linker_sizes(ld_file: str):
    """Very hacky way to read flash/ram size from ld file. """
    try:
        print(ld_file)
        with open(ld_file, 'r', encoding='utf-8') as f:
            all = f.read()
            flash = re.findall('FLASH.*ORIGIN\s*=\s*(\w*),\s*LENGTH\s*=\s*(\w*)', all)[0]
            ram = re.findall('RAM.*ORIGIN\s*=\s*(\w*),\s*LENGTH\s*=\s*(\w*)', all)[0]
            return parse_num(flash[1]), parse_num(ram[1])
    except IndexError:
        return None
    return None


ldscript = board.get('build.ldscript', '')
if  not ldscript:
    raise RuntimeError('Board has no ldscript!')
ldscript = join(FRAMEWORK_DIR, 'ldscripts', ldscript)
env.Replace(LDSCRIPT_PATH=ldscript)

sizes = get_linker_sizes(ldscript)
board.update("upload.maximum_size", str(sizes[0]))
board.update("upload.maximum_ram_size", str(sizes[1]))


# if sdk_files:
#     env.BuildSources(
#         join("$BUILD_DIR", "sdk_files"),
#         sdk_dir,
#         ['+<{}>'.format(s) for s in sdk_files]
#     )

env.BuildSources(
    join('$BUILD_DIR', 'Driver'),
    join(driver_dir, 'Src'),
)

env.BuildSources(
    join('$BUILD_DIR', 'BSP'),
    join(bsp_dir, 'Src'),
)


libs = []

def select_best_file(path, filemask, mcu):
    presize_file = filemask.format(mcu)  # e.g. system_py32f003.c
    filemask = filemask.format('.*')
    files = [p for p in listdir(path) if re.match(filemask, p)]

    for f in files:
        if re.match(f.replace('x', '.'), presize_file):
            print(f)
            return f
    return None


cmsis_src_dir = join(dir_cmsis, 'Device', 'PY32F0xx', 'Source')
libs.append(
    env.BuildLibrary(
        join("$BUILD_DIR", "FrameworkCMSISDevice"),
        cmsis_src_dir,
        src_filter=[
            '-<*>',
            '+<gcc/startup_{}.S>'.format(mcu_short.lower()),
            '+<{}>'.format(select_best_file(cmsis_src_dir, 'system_{}.c', mcu_short.lower())),
        ],
    )
)

env.Prepend(LIBS=libs)

