import os
import sys
from platform import system
from os import makedirs
from os.path import isdir, join, basename

from SCons.Script import (ARGUMENTS, COMMAND_LINE_TARGETS, AlwaysBuild,
                          Builder, Default, DefaultEnvironment)

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

self_dir = os.path.dirname(env.subst('$BUILD_SCRIPT'))
platform_dir = os.path.abspath(join(self_dir, '..'))

env.Replace(
    AR="arm-none-eabi-ar",
    AS="arm-none-eabi-as",
    CC="arm-none-eabi-gcc",
    CXX="arm-none-eabi-g++",
    GDB="arm-none-eabi-gdb",
    OBJCOPY="arm-none-eabi-objcopy",
    RANLIB="arm-none-eabi-ranlib",
    SIZETOOL="arm-none-eabi-size",

    ARFLAGS=["rc"],

    SIZEPROGREGEXP=r"^(?:\.text|\.data|\.rodata|\.text.align|\.ARM.exidx)\s+(\d+).*",
    SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit)\s+(\d+).*",
    SIZECHECKCMD="$SIZETOOL -A -d $SOURCES",
    SIZEPRINTCMD='$SIZETOOL -B -d $SOURCES',

    PROGSUFFIX=".elf"
)

# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")

env.Append(
    BUILDERS=dict(
        ElfToBin=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "binary",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET bin"),
            suffix=".bin"
        ),
        ElfToHex=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "ihex",
                "-R",
                ".eeprom",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET hex"),
            suffix=".hex"
        ),
        HexToElf=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-I",
                "ihex",
                "-O",
                "elf32-littlearm",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET elf from hex"),
            suffix=".elf"
        ),
))

upload_protocol = env.subst("$UPLOAD_PROTOCOL")


if not env.get("PIOFRAMEWORK"):
    env.SConscript("frameworks/_bare.py")

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
    target_firm = join("$BUILD_DIR", "${PROGNAME}.hex")
else:
    target_elf = env.BuildProgram()
    target_firm = target_elf  # TODO: can require conversion to e.g. .hex

AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm)

#
# Target: Print binary size
#

target_size = env.AddPlatformTarget(
    "size",
    target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"),
    "Program Size",
    "Calculate program size",
)

#
# Target: Upload file
#

debug_tools = env.BoardConfig().get("debug.tools", {})
upload_actions = []

if upload_protocol.startswith("blackmagic"):
    env.Replace(
        UPLOADER="$GDB",
        UPLOADERFLAGS=[
            "-nx",
            "--batch",
            "-ex", "target extended-remote $UPLOAD_PORT",
            "-ex", "monitor %s_scan" %
            ("jtag" if upload_protocol == "blackmagic-jtag" else "swdp"),
            "-ex", "attach 1",
            "-ex", "load",
            "-ex", "compare-sections",
            "-ex", "kill"
        ],
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS $SOURCE"
    )
    upload_actions = [
        env.VerboseAction(env.AutodetectUploadPort, "Looking for BlackMagic port..."),
        env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")
    ]

elif upload_protocol.startswith("jlink"):

    def _jlink_cmd_script(env, source):
        build_dir = env.subst("$BUILD_DIR")
        if not isdir(build_dir):
            makedirs(build_dir)
        script_path = join(build_dir, "upload.jlink")
        commands = [
            "halt",
            "loadfile %s" % source,
            "reset",
            "exit",
        ]

        with open(script_path, "w") as fp:
            fp.write("\n".join(commands))
        return script_path

    env.Replace(
        __jlink_cmd_script=_jlink_cmd_script,
        UPLOADER="JLink.exe" if system() == "Windows" else "JLinkExe",
        UPLOADERFLAGS=[
            "-device", env.BoardConfig().get("debug", {}).get("jlink_device"),
            "-speed", env.GetProjectOption("debug_speed", "4000"),
            "-if", ("jtag" if upload_protocol == "jlink-jtag" else "swd"),
            "-autoconnect", "1",
            "-NoGui", "1"
        ],
        UPLOADCMD='$UPLOADER $UPLOADERFLAGS -CommanderScript "${__jlink_cmd_script(__env__, SOURCE)}"'
    )
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

elif upload_protocol in debug_tools:
    print('OpenOCD is not (yet) supported!')
    openocd_args = [
        "-d%d" % (2 if int(ARGUMENTS.get("PIOVERBOSE", 0)) else 1)
    ]
    openocd_args.extend(
        debug_tools.get(upload_protocol).get("server").get("arguments", []))
    if env.GetProjectOption("debug_speed"):
        openocd_args.extend(
            ["-c", "adapter speed %s" % env.GetProjectOption("debug_speed")]
        )
    openocd_args.extend([
        "-c", "program {$SOURCE} %s verify reset; shutdown;" %
        board.get("upload.offset_address", "")
    ])
    openocd_args = [
        f.replace("$PACKAGE_DIR",
                  platform.get_package_dir("tool-openocd") or "")
        for f in openocd_args
    ]
    env.Replace(
        UPLOADER="openocd",
        UPLOADERFLAGS=openocd_args,
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS")
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

env.AddPlatformTarget("upload", target_firm, upload_actions, "Upload")

#
# Information about obsolete method of specifying linker scripts
#

if any("-Wl,-T" in f for f in env.get("LINKFLAGS", [])):
    print("Warning! '-Wl,-T' option for specifying linker scripts is deprecated. "
          "Please use 'board_build.ldscript' option in your 'platformio.ini' file.")

#
# Default targets
#

Default([target_buildprog, target_size])
