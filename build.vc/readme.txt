Building FLINT2 with Microsoft Visual Studio
-------------------------------------------------

Building FLINT2 with Microsoft Visual Studio requires Visual
Visual Studio 2015 Community (or higher version) and:

    a) an installed version of Python 3
    b) an installed version of Python Tools for 
       Visual Studio (http://pytools.codeplex.com/)

Obtain FLINT2 either as a released distribution or clone it using
GIT from:

    git@github.com:BrianGladman/flint.git

FLINT2 depends on the MPIR, MPFR and PTHREADS libraries that have
to be installed and built using Visual Studio before FLINT2 can
be built.  The application directories are assumed to be in the
same root directory with the names and layouts:
   
    mpir
       lib
       dll
    mpfr  
       lib
       dll
    pthreads  
       lib
       dll
    flint
       build.vc
       lib
       dll
 
Here the lib and dll sub-directories for each application hold the 
static and dynamic link library outputs which will be used when 
Flint is built. They each contain up to four sub-directories for 
the normal configurations for building on Windows:

    Win32\Release

    Win32\Debug

    x64\Release

    x64\Debug

To build FLINT2 for a particular configuration requires that each
of the three libraries on which FLINT2 depends must have been 
previously built for the same configuration.

Opening the solution file flint\build.vc\flint.sln provides the 
following build projects:

flint_config - a Python program for creating the Visual Studio 
               build files

build_tests -  a Python program for building the FLINT2 tests 
               (after they have been created)

run_tests -   a Python program for running the FLINT2 tests 
              (after they have been built)

The first step in building FLINT2 is to generate the Visual 
Studio build files for the version of Visual Studio being used. 
This is done by running the Python application flint_config.py, 
either from within Visual Studio or on the command line. It is 
run with a single input parameter which is the last two digits 
of the Visual Studio version selected for building FLINT2 (the 
default is 19 if no input is given).

Ths creates a build directory in the Flint root directory, for 
example:

    flint\build.vs19

that contains the file flint.sln which can now be loaded into 
Visual Studio and used to build the FLINT2 library.
  
Once the FLINT2 library has been built, the FLINT2 tests can now 
be built and run by returning to the Visual Studio solution:

    flint\build.vc\flint.sln

and running the build_tests and run_tests Python applications.

After building FLINT2, the libraries and the header files that
you need to use FLINT2 are placed in the directories in the
FLINT root directory:

lib\<Win32|x64>\<Debug|Release>

dll\<Win32|x64>\<Debug|Release>

depending on the version(s) that have been built.
   
      Brian Gladman
      24th June 2020

