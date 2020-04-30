# generate vcxproj file

from os.path import normpath, join, split, relpath
from os import access, F_OK
from enum import IntEnum

class Project_Type(IntEnum):
  APP = 0
  LIB = 1
  DLL = 2

app_ext = ('.exe', '.lib', '.dll')
app_str = ('Application', 'StaticLibrary', 'DynamicLibrary')

def vcx_proj_cfg(plat, outf):

  f1 = r'''  <ItemGroup Label="ProjectConfigurations">
'''
  f2 = r'''    <ProjectConfiguration Include="{1:s}|{0:s}">
      <Configuration>{1:s}</Configuration>
      <Platform>{0:s}</Platform>
    </ProjectConfiguration>
'''
  f3 = r'''  </ItemGroup>
'''
  outf.write(f1)
  for pl in plat:
    for conf in ('Release', 'Debug'):
      outf.write(f2.format(pl, conf))
  outf.write(f3)

def vcx_globals(name, guid, vs_info, outf):

  f1 = r'''  <PropertyGroup Label="Globals">
    <RootNamespace>{0:s}</RootNamespace>
    <Keyword>Win32Proj</Keyword>
    <ProjectGuid>{1:s}</ProjectGuid>
    <WindowsTargetPlatformVersion>{2:s}</WindowsTargetPlatformVersion>
  </PropertyGroup>
'''
  outf.write(f1.format(name, guid, vs_info['windows_sdk']))

def vcx_default_cpp_props(outf):

  f1 = r'''  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.Default.props" />
'''
  outf.write(f1)

def vcx_library_type(plat, proj_type, vs_info, outf):

  f1 = r'''  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='{1:s}|{0:s}'" Label="Configuration">
    <ConfigurationType>{2:s}</ConfigurationType>
    <UseDebugLibraries>{3:s}</UseDebugLibraries>
    <PlatformToolset>v{4:s}</PlatformToolset>
  </PropertyGroup>
'''
  for pl in plat:
    for conf, bool in (('Release', 'false'), ('Debug', 'true')):
      outf.write(f1.format(pl, conf, app_str[proj_type], bool, vs_info['platform_toolset']))

def vcx_cpp_props(outf):

  f1 = r'''  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.props" />
'''
  outf.write(f1)

def vcx_extensions(outf, dir):

  f1 = r'''  <ImportGroup Label="ExtensionSettings">
    <Import Project="{0:s}vsyasm.props" />
  </ImportGroup>
'''
  outf.write(f1.format(dir))

def vcx_user_props(plat, proj_type, outf):

  f1 = r'''  <ImportGroup Condition="'$(Configuration)|$(Platform)'=='{1:s}|{0:s}'" Label="PropertySheets">
    <Import Project="$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props" Condition="exists('$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props')" />
    <Import Project="..\..\{4:s}build.vc\flint_{2:s}_{3:s}.props" />
  </ImportGroup>
'''
  depth = '..\\' if proj_type == Project_Type.APP else ''
  for pl in plat:
    for conf in ('Release', 'Debug'):
      outf.write(f1.format(pl, conf, conf.lower(), app_ext[proj_type][1:], depth))

def vcx_target_name_and_dirs(proj_name, proj_dir, plat, outf):

  f1 = r'''  <PropertyGroup>
    <_ProjectFileVersion>10.0.21006.1</_ProjectFileVersion>
'''
  f2 = r'''    <TargetName Condition="'$(Configuration)|$(Platform)'=='{1:s}|{0:s}'">{2:s}</TargetName>
    <IntDir Condition="'$(Configuration)|$(Platform)'=='{1:s}|{0:s}'">$(Platform)\$(Configuration)\</IntDir>
    <OutDir Condition="'$(Configuration)|$(Platform)'=='{1:s}|{0:s}'">$(SolutionDir){3:s}$(Platform)\$(Configuration)\</OutDir>
    <LinkIncremental>false</LinkIncremental>
'''
  f3 = r'''  </PropertyGroup>
'''
  if not proj_dir:
    proj_dir = ''
  elif not (proj_dir.endswith('\\') or proj_dir.endswith('/')):
    proj_dir += '\\'

  outf.write(f1)
  for pl in plat:
    for conf in ('Release', 'Debug'):
      outf.write(f2.format(pl, conf, proj_name, proj_dir))
  outf.write(f3)

def compiler_options(plat, proj_type, is_debug, inc_dirs, flib_type, outf):

  f1 = r'''    <ClCompile>
    <Optimization>{0:s}</Optimization>
    <IntrinsicFunctions>true</IntrinsicFunctions>
    <AdditionalIncludeDirectories>{1:s}</AdditionalIncludeDirectories>
    <PreprocessorDefinitions>{2:s}%(PreprocessorDefinitions)</PreprocessorDefinitions>
    <RuntimeLibrary>MultiThreaded{3:s}</RuntimeLibrary>
    <ProgramDataBaseFileName>$(TargetDir)$(TargetName).pdb</ProgramDataBaseFileName>
    <DebugInformationFormat>{4:s}</DebugInformationFormat>
    </ClCompile>
'''

  if proj_type == Project_Type.APP:
    s1 = 'DEBUG;WIN32;_CONSOLE;PTW32_STATIC_LIB;'
    s2 = ''
  if proj_type == Project_Type.DLL:
    s1 = 'DEBUG;WIN32;HAVE_CONFIG_H;FLINT_BUILD_DLL;PTW32_BUILD;'
    s2 = 'DLL'
  elif proj_type == Project_Type.LIB:
    s1 = 'DEBUG;WIN32;_LIB;HAVE_CONFIG_H;PTW32_STATIC_LIB;'
    s2 = ''
  else:
    pass
  if flib_type == 'single':
    s1 += 'FLINT_REENTRANT=0;HAVE_TLS=1;'
  elif flib_type == 'reentrant':
    s1 += 'FLINT_REENTRANT=1;HAVE_TLS=1;'
  else:
    pass
  if plat == 'x64':
    s1 = s1 + '_WIN64;'
  if is_debug:
    opt, defines, crt, dbf = 'Disabled', '_' + s1, 'Debug' + s2, 'ProgramDatabase'
  else:
    opt, defines, crt, dbf = 'Full', 'N' + s1, s2, 'None'
  outf.write(f1.format(opt, inc_dirs, defines, crt, dbf))

def linker_options(name, link_libs, proj_type, debug_info, outf):

  f1 = r'''    <Link>
'''
  f2 = r'''      <GenerateDebugInformation>true</GenerateDebugInformation>
'''
  f3 = r'''      <LargeAddressAware>true</LargeAddressAware>
      <AdditionalDependencies>{}%(AdditionalDependencies)</AdditionalDependencies>
'''
  f4 = '''      <ModuleDefinitionFile>$(SolutionDir){}.def</ModuleDefinitionFile>
'''
  f5 = '''    </Link>
'''
  outf.write(f1)
  if debug_info:
    outf.write(f2)
  outf.write(f3.format(link_libs))
  # no longer needed as we are using the declspec approach
  #  if proj_type == Project_Type.DLL:
  #    outf.write(f4.format(name))
  outf.write(f5)

def vcx_pre_build(outf):

  f1 = r'''    <PreBuildEvent>
        <Command>..\..\build.vc\out_copy_rename.bat ..\..\build.vc\cpimport.h ..\..\qadic\ cpimport.h
        </Command>
        <Command>..\..\build.vc\out_copy_rename.bat ..\..\build.vc\config.h ..\..\ flint-config.h
        </Command>
    </PreBuildEvent>
'''

  outf.write(f1)

def vcx_post_build(proj_type, msvc_ver, outf):

  f1 = r'''
  <PostBuildEvent>
      <Command>..\..\build.vc\postbuild $(IntDir) {} {}
      </Command>
  </PostBuildEvent>
'''

  outf.write(f1.format((app_ext[proj_type][1:]).upper(), msvc_ver))

def vcx_tool_options(name, plat, proj_type, prebuild, postbuild, inc_dirs, link_libs, debug_info, msvc_ver, flib_type, outf):

  f1 = r'''  <ItemDefinitionGroup Condition="'$(Configuration)|$(Platform)'=='{1:s}|{0:s}'">
'''
  f2 = r'''  </ItemDefinitionGroup>
'''
  for pl in plat:
    for is_debug in (False, True):
      outf.write(f1.format(pl, 'Debug' if is_debug else 'Release'))
      if prebuild:
        vcx_pre_build(outf)
      compiler_options(pl, proj_type, is_debug, inc_dirs, flib_type, outf)
      if proj_type != Project_Type.LIB:
        linker_options(name, link_libs, proj_type, debug_info, outf)
      if postbuild:
        vcx_post_build(proj_type, msvc_ver, outf)
      outf.write(f2)

def vcx_external_props(outf):

  f1 = r'''  <ImportGroup>
    <Import Condition="exists('$(MPIR_Props_External)')" Project="$(MPIR_Props_External)" />
  </ImportGroup>
'''
  outf.write(f1)

def vcx_hdr_items(hdr_list, relp, outf):

  f1 = r'''  <ItemGroup>
'''
  f2 = r'''    <ClInclude Include="{}{}" />
'''
  f3 = r'''  </ItemGroup>
'''
  outf.write(f1)
  for i in hdr_list:
    outf.write(f2.format(relp, i))
  outf.write(f3)

def vcx_c_items(cf_list, plat, relp, flib_type, outf):

  f1 = r'''  <ItemGroup>
'''
  f2 = r'''    <ClCompile Include="{}{}" />
'''
  f3 = r'''    <ClCompile Include="{}{}">
'''
  f4 = r'''        <ObjectFileName Condition="'$(Configuration)|$(Platform)'=='{0:s}|{1:s}'">$(IntDir){2:s}\</ObjectFileName>
'''
  f5 = r'''      <ExcludedFromBuild Condition="'$(Configuration)|$(Platform)'=='{0:s}|{1:s}'">true</ExcludedFromBuild>
'''
  f6 = r'''    </ClCompile>
'''
  f7 = r'''  </ItemGroup>
'''

  outf.write(f1)
  for nxd in cf_list:
    if nxd[0] == 'link':
      ts = split(nxd[1])[1]
      ts = ts.replace('fmpz_', '')
      ts = ts.replace('.c', '')
      if ts != flib_type:
        outf.write(f3.format(relp, nxd[1]))
        for cf in ('Release', 'Debug'):
          for pl in plat:
            outf.write(f5.format(cf, pl))
        outf.write(f6)
        continue
    outf.write(f2.format(relp, nxd[1]))
  outf.write(f7)

def gen_vcxproj(path, root_dir, proj_name, guid, plat, proj_type, flib_type, prebuild, postbuild, debug_info, hf_list, cf_list, inc_dirs, link_libs, vs_info):

  f1 = r'''<?xml version="1.0" encoding="utf-8"?>
<Project DefaultTargets="Build" ToolsVersion="{}" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
'''
  f2 = r'''  <PropertyGroup Label="UserMacros" />
'''
  f3 = r'''  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />
</Project>
'''

  relp = split(relpath(root_dir, path))[0] + '\\'
  project_dir = ''
  with open(path, 'w') as outf:
    outf.write(f1.format(vs_info['vcx_tool']))
    vcx_proj_cfg(plat, outf)
    vcx_globals(proj_name, guid, vs_info, outf)
    vcx_default_cpp_props(outf)
    vcx_library_type(plat, proj_type, vs_info, outf)
    vcx_cpp_props(outf)
    vcx_user_props(plat, proj_type, outf)
    outf.write(f2)
    vcx_target_name_and_dirs(proj_name, project_dir, plat, outf)
    vcx_tool_options(proj_name, plat, proj_type, prebuild, postbuild, inc_dirs, link_libs, debug_info, vs_info['msvc'], flib_type, outf)
    vcx_external_props(outf)
    if hf_list:
      vcx_hdr_items(hf_list, relp, outf)
    vcx_c_items(cf_list, plat, relp, flib_type, outf)
    outf.write(f3)
