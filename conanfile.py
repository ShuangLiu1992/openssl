from conan import ConanFile
import conan.tools.files
from conan.tools.microsoft import unix_path, VCVars
from conan.tools.env import Environment
from conan.tools.env import VirtualBuildEnv
import os


class OpenSSLConan(ConanFile):
    name = "openssl"
    settings = "os", "build_type", "compiler", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def build_requirements(self):
        if self.settings_build.os == "Windows":
            if self.settings.os != "Windows":
                self.win_bash = True
                self.tool_requires(f"msys2/{self.version}@")
            else:
                self.tool_requires(f"jom/{self.version}@")
                self.tool_requires(f"strawberryperl/{self.version}@")
                self.tool_requires(f"nasm/{self.version}@")

    def source(self):
        conan.tools.files.get(self,"https://github.com/openssl/openssl/archive/refs/tags/openssl-3.0.7.tar.gz", strip_root=True,
                  md5="22142b9840527fd0e4b9c8dd2151084d")

    def generate(self):
        if self.settings.compiler == "msvc":
            ms = VCVars(self)
            ms.generate()

    def build(self):
        target = ""
        flags = ""
        if self.settings.compiler == "msvc":
            target = "VC-WIN64A"
            flags = "/FS"
        if self.settings.os == "Android":
            arch = {"armv8": "arm64", "armv7": "arm"}.get(str(self.settings.arch), str(self.settings.arch))
            target = f"android-{arch}"
        if self.settings.os == "Linux":
            flags = "'-Wl,--enable-new-dtags,-rpath,$(LIBRPATH)'"
        build_type = "-d" if self.settings.build_type == "Debug" else ""
        install_dir = unix_path(self, self.package_folder)
        shared = "" if self.options.shared else "no-shared"
        if self.settings.compiler == "msvc":
            self.run(f'perl Configure {target} {build_type} {shared} no-tests --prefix={install_dir} --openssldir={install_dir} {flags}')
            self.run(f'jom')
            self.run(f'nmake install_sw')
        else:
            self.run(
                f"./Configure {target} {build_type} {shared} no-tests --prefix={install_dir} --openssldir={install_dir} {flags}")
            self.run("make -j16")
            self.run('make install_sw -j16')

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
