import os
import platform
import subprocess
import shutil
import sys

class Settings:
    def __init__(self):
        self.mBuildTarget = ''
        self.mHostName = ''
        self.mAndroidApi = ''
        self.mAndroidNdkDir = ''
        self.mCoreCount = ''
        self.mMake = ''
        self.mBuildDir = ''
        self.mToolchainRemovable = False
        self.mToolchainDir = ''
        self.mToolchainArch = []
        self.mToolchainName = []
        self.mArch = []
        self.mArchFlag = []
        self.mArchName = []
        self.mMakeFlag = []
        
def downloadAndExtract(pURL, pDestinationDir, pFileName, pExtractDir):
    import io
    import ssl
    import urllib.error
    import urllib.request
    import zipfile
    
    print('Downloading and extracting...')

    status = False
    downloadContent = None

    try:
        context = ssl._create_unverified_context()
        downloadContent = urllib.request.urlopen(pURL, context = context).read()
    except urllib.error.HTTPError as e:
        print('Failed')
    except urllib.error.URLError as e:
        print('Failed')
    
    if downloadContent is not None and len(downloadContent) > 0:
        archiveFile = zipfile.ZipFile(io.BytesIO(downloadContent), "r")
        archiveFile.extractall(os.path.join(pDestinationDir, pExtractDir))
        archiveFile.close()
        status = True
        
    return status
    
def prepareMake(pDestinationDir):
    print('Preparing \'make\'...')

    status = False

    destinationMakePath = os.path.join(pDestinationDir, 'make.exe')
    destinationIconvPath = os.path.join(pDestinationDir, 'libiconv2.dll')
    destinationIntlPath = os.path.join(pDestinationDir, 'libintl3.dll')
    
    if not os.path.isfile(destinationMakePath):
        if downloadAndExtract('https://sourceforge.net/projects/gnuwin32/files/make/3.81/make-3.81-bin.zip/download', pDestinationDir, 'make-3.81-bin.zip', 'make-3.81-bin'):
            extractDir = os.path.join(pDestinationDir, 'make-3.81-bin')
            binDir = os.path.join(extractDir, 'bin')
            shutil.copy2(os.path.join(binDir, 'make.exe'), destinationMakePath)
            shutil.rmtree(extractDir)
            os.remove(extractDir + '.zip')
     
    if not os.path.isfile(destinationIconvPath) or not os.path.isfile(destinationIntlPath):
        if downloadAndExtract('https://sourceforge.net/projects/gnuwin32/files/make/3.81/make-3.81-dep.zip/download', pDestinationDir, 'make-3.81-dep.zip', 'make-3.81-dep'):
            extractDir = os.path.join(pDestinationDir, 'make-3.81-dep')
            binDir = os.path.join(extractDir, 'bin')
            shutil.copy2(os.path.join(binDir, 'libiconv2.dll'), destinationIconvPath)
            shutil.copy2(os.path.join(binDir, 'libintl3.dll'), destinationIntlPath)
            shutil.rmtree(extractDir)
            os.remove(extractDir + '.zip')

    return os.path.isfile(destinationMakePath) and os.path.isfile(destinationIconvPath) and os.path.isfile(destinationIntlPath)
        
def configure(pSettings):
    import multiprocessing

    print('Configuring...')

    if sys.version_info < (3, 0):
        print('Error: This script requires Python 3.0 or higher. Please use "python3" command instead of "python".')
        return False
    
    if len(sys.argv) < 1 or sys.argv[1] is None or (sys.argv[1] != 'android' and sys.argv[1] != 'linux'):
        print('Error: Missing or wrong build target. Following targets are supported: "android", "linux".')
        return False

    workingDir = os.getcwd()
    pSettings.mBuildTarget = sys.argv[1]
    pSettings.mHostName = platform.system()
    pSettings.mBuildDir = os.path.join(workingDir, 'build')

    if pSettings.mBuildTarget == 'android':
        hostDetected = False
        
        if pSettings.mHostName == 'Linux' or pSettings.mHostName == 'Darwin':
            hostDetected = True
            
            if os.path.isfile('/usr/bin/make'):
                pSettings.mMake = '/usr/bin/make'
            else:
                print('Error: /usr/bin/make not found.')
                return False
        elif pSettings.mHostName == 'Windows':
            hostDetected = True
            
            if prepareMake(pSettings.mBuildDir):
                pSettings.mMake = os.path.join(pSettings.mBuildDir, 'make.exe')
            else:
                print('Error: make.exe not found.')
                return False
    
        if hostDetected:
            androidApi = os.getenv('HERMES_ANDROID_API')
           
            name, separator, version = None, None, None
            
            if androidApi is not None:
                name, separator, version = androidApi.partition('-')
            
            if version is not None and len(version) > 0:
                pSettings.mAndroidApi = version
            else:
                pSettings.mAndroidApi = name
            
            pSettings.mAndroidNdkDir = os.getenv('ANDROID_NDK_ROOT')

            if pSettings.mAndroidApi is None:
                pSettings.mAndroidApi = '21'

            if pSettings.mAndroidNdkDir is None or not os.path.isdir(pSettings.mAndroidNdkDir):
                androidHome = os.getenv('ANDROID_HOME')
                
                if androidHome is not None and os.path.isdir(androidHome):
                    pSettings.mAndroidNdkDir = os.path.join(androidHome, 'ndk-bundle')
                    
                    if not os.path.isdir(pSettings.mAndroidNdkDir):
                        print('Error: ' + pSettings.mAndroidNdkDir + ' is not a valid path.')
                        return False
                else:
                    print('Error: Occurred problem related to ANDROID_HOME environment variable.')
                    return False
            
            pSettings.mToolchainDir = os.path.join(workingDir, 'toolchain')
            pSettings.mToolchainArch = ['arm', 'arm64', 'x86', 'x86_64']
            pSettings.mToolchainName = ['arm-linux-androideabi', 'aarch64-linux-android', 'i686-linux-android', 'x86_64-linux-android']
            pSettings.mArch = ['android-armeabi', 'android64-aarch64', 'android-x86', 'android64']
            pSettings.mArchFlag = ['-march=armv7-a -mfloat-abi=softfp -mfpu=vfpv3-d16 -mthumb -mfpu=neon', '', '-march=i686 -m32 -mtune=intel -msse3 -mfpmath=sse', '-march=x86-64 -m64 -mtune=intel -msse4.2 -mpopcnt']
            pSettings.mArchName = ['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64']
            pSettings.mMakeFlag = ['', 'ARCH64=1', '', 'ARCH64=1']

            print('Android API: "' + pSettings.mAndroidApi + '"')
            print('Android NDK path: "' + pSettings.mAndroidNdkDir + '"')
        else:
            print('Error: Not supported host platform: ' + pSettings.mHostName + '.')
            return False
    elif pSettings.mBuildTarget == 'linux':
        hostDetected = False
        
        if pSettings.mHostName == 'Linux':
            hostDetected = True
            
            if os.path.isfile('/usr/bin/make'):
                pSettings.mMake = '/usr/bin/make'
            else:
                print('Error: /usr/bin/make not found.')
                return False

        if hostDetected:
            pSettings.mArchFlag = ['-m32', '-m64']
            pSettings.mArchName = ['x86', 'x86_64']
            pSettings.mMakeFlag = ['', '']
            pSettings.mMakeFlag = ['', 'ARCH64=1']
        else:
            print('Error: Not supported host platform: ' + pSettings.mHostName + '.')
            return False
    else:
        return False
        
    pSettings.mCoreCount = str(multiprocessing.cpu_count())
        
    print('Available CPU cores: ' + pSettings.mCoreCount)
    
    return True
         
def prepareToolchain(pSettings):
    if pSettings.mBuildTarget == 'android':
        print('Preparing toolchains...')

        for i in range(0, len(pSettings.mArch)):
            destinationPath = os.path.join(pSettings.mToolchainDir, pSettings.mToolchainArch[i])
            if not os.path.isdir(destinationPath):
                androidApi = pSettings.mAndroidApi
                if (int(androidApi) < 21 and (pSettings.mToolchainArch[i] == 'arm64' or pSettings.mToolchainArch[i] == 'x86_64')):
                    androidApi = '21'
                    print('Force Android API: \"21\" for architecture \"' + pSettings.mToolchainArch[i] + '\".')
                os.system(os.path.join(pSettings.mAndroidNdkDir, 'build', 'tools', 'make_standalone_toolchain.py') + ' --arch ' + pSettings.mToolchainArch[i] + ' --api ' + androidApi + ' --stl libc++ --install-dir ' + destinationPath)

        pSettings.mToolchainRemovable = True
        return

def executeShellCommand(pCommandLine):
    process = subprocess.Popen(pCommandLine, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)        
    output, error = process.communicate()
    returnCode = process.wait()
    
    print(output.decode())

    if returnCode != 0:
        print('Error message:\n' + error.decode("utf-8"))
    
    return returnCode
    
def executeCmdCommand(pCommandLine, pWorkingDir):
    commandLine = pCommandLine.encode()    
    commandLine += b"""
    exit
    """

    process = subprocess.Popen(["cmd", "/q", "/k", "echo off"], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, cwd = pWorkingDir, shell = True)
    process.stdin.write(commandLine)
    output, error = process.communicate()
    returnCode = process.wait()
    
    print(output.decode())

    if returnCode != 0:
        print('Error message:\n' + error.decode("utf-8"))
    
    return returnCode
    
def remove(pPath):
    if pPath is not None:
        if os.path.isdir(pPath):
            shutil.rmtree(pPath)
        elif os.path.isfile(pPath):
            os.remove(pPath)
            
    return

def cleanup(pSettings):
    print('Cleaning...')

    if pSettings.mToolchainRemovable:
        remove(pSettings.mToolchainDir)
        
    return

def buildMake(pRootDir, pLibraryName, pSettings, pMakeFlag):
    status = False
    if pSettings.mBuildTarget == 'android':
        status = buildMakeAndroid(pRootDir, pLibraryName, pSettings, pMakeFlag)
    elif pSettings.mBuildTarget == 'linux':
        status = buildMakeLinux(pRootDir, pLibraryName, pSettings, pMakeFlag)
    return status
    
def buildMakeAndroid(pRootDir, pLibraryName, pSettings, pMakeFlag):
    print('Building...')
    status = False
    workingDir = os.getcwd()
    
    if pSettings.mHostName == 'Linux' or pSettings.mHostName == 'Darwin':
        executeShellCommand(pSettings.mMake + ' clean')
    elif pSettings.mHostName == 'Windows':
        executeCmdCommand(pSettings.mMake + ' clean', workingDir)

    for i in range(0, len(pSettings.mArchName)):
        toolchainBinDir = os.path.join(pSettings.mToolchainDir, pSettings.mToolchainArch[i], 'bin')
        libraryDir = os.path.join(pRootDir, 'lib', 'android', pSettings.mArchName[i])

        if not os.path.isdir(libraryDir):
            os.makedirs(libraryDir)
        else:
            for j in range(0, len(pLibraryName)):
                libraryFilepath = os.path.join(libraryDir, 'lib' + pLibraryName[j] + '.a')
                
                if os.path.isfile(libraryFilepath):
                    os.remove(libraryFilepath)
        
        if os.path.isdir(toolchainBinDir):
            executablePrefix = os.path.join(toolchainBinDir, pSettings.mToolchainName[i])
        
            os.environ['CXX'] = executablePrefix + '-clang++'
            os.environ['CC'] = executablePrefix + '-clang'
            os.environ['LD'] = executablePrefix + '-ld'
            os.environ['AR'] = executablePrefix + '-ar'
            os.environ['RANLIB'] = executablePrefix + '-ranlib'
            os.environ['STRIP'] = executablePrefix + '-strip'
            
            envSYSROOT = os.path.join(pSettings.mToolchainDir, pSettings.mToolchainArch[i], 'sysroot')        
            envCXXFLAGS = pSettings.mArchFlag[i] + ' --sysroot=' + envSYSROOT
            envCFLAGS = pSettings.mArchFlag[i] + ' --sysroot=' + envSYSROOT

            os.environ['SYSROOT'] = envSYSROOT
            os.environ['CXXFLAGS'] = envCXXFLAGS
            os.environ['CFLAGS'] = envCFLAGS

            makeCommand = pSettings.mMake + ' -j' + pSettings.mCoreCount
            
            for j in range(0, len(pLibraryName)):
                makeCommand += ' lib' + pLibraryName[j] + '.a'
 
            if len(pSettings.mMakeFlag[i]) > 0:
                makeCommand += ' ' + pSettings.mMakeFlag[i]
                
            if pMakeFlag is not None and len(pMakeFlag) > 0:
                makeCommand += ' ' + pMakeFlag
                
            for j in range(2, len(sys.argv)):
                makeCommand += ' ' + sys.argv[j]
                
            buildSuccess = False

            if pSettings.mHostName == 'Linux' or pSettings.mHostName == 'Darwin':
                buildSuccess = executeShellCommand(makeCommand) == 0
            elif pSettings.mHostName == 'Windows':
                buildSuccess = executeCmdCommand(makeCommand, workingDir) == 0
                
            if buildSuccess:
                for j in range(0, len(pLibraryName)):
                    try:
                        shutil.copy2(os.path.join(workingDir, 'lib' + pLibraryName[j] + '.a'), os.path.join(libraryDir, 'lib' + pLibraryName[j] + '.a'))
                    except FileNotFoundError:
                        pass

            if pSettings.mHostName == 'Linux' or pSettings.mHostName == 'Darwin':
                executeShellCommand(pSettings.mMake + ' clean')
            elif pSettings.mHostName == 'Windows':
                executeCmdCommand(pSettings.mMake + ' clean', workingDir)
                
            print('Build status for ' + pSettings.mArchName[i] + ': ' + ('Succeeded' if buildSuccess else 'Failed') + '\n')
            
            status |= buildSuccess
        
    return status
    
def buildMakeLinux(pRootDir, pLibraryName, pSettings, pMakeFlag):
    print('Building...')
    status = False
    workingDir = os.getcwd()

    executeShellCommand(pSettings.mMake + ' clean')

    for i in range(0, len(pSettings.mArchName)):
        libraryDir = os.path.join(pRootDir, 'lib', 'linux', pSettings.mArchName[i])

        if not os.path.isdir(libraryDir):
            os.makedirs(libraryDir)
        else:
            for j in range(0, len(pLibraryName)):
                libraryFilepath = os.path.join(libraryDir, 'lib' + pLibraryName[j] + '.a')
                
                if os.path.isfile(libraryFilepath):
                    os.remove(libraryFilepath)
      
        envCXXFLAGS = pSettings.mArchFlag[i]
        envCFLAGS = pSettings.mArchFlag[i]

        os.environ['CXXFLAGS'] = envCXXFLAGS
        os.environ['CFLAGS'] = envCFLAGS

        makeCommand = pSettings.mMake + ' -j' + pSettings.mCoreCount
        
        for j in range(0, len(pLibraryName)):
            makeCommand += ' lib' + pLibraryName[j] + '.a'

        if len(pSettings.mMakeFlag[i]) > 0:
            makeCommand += ' ' + pSettings.mMakeFlag[i]
            
        if pMakeFlag is not None and len(pMakeFlag) > 0:
            makeCommand += ' ' + pMakeFlag
            
        for j in range(2, len(sys.argv)):
            makeCommand += ' ' + sys.argv[j]
            
        buildSuccess = executeShellCommand(makeCommand) == 0
            
        if buildSuccess:
            for j in range(0, len(pLibraryName)):
                try:
                    shutil.copy2(os.path.join(workingDir, 'lib' + pLibraryName[j] + '.a'), os.path.join(libraryDir, 'lib' + pLibraryName[j] + '.a'))
                except FileNotFoundError:
                    pass

        executeShellCommand(pSettings.mMake + ' clean')
            
        print('Build status for ' + pSettings.mArchName[i] + ': ' + ('Succeeded' if buildSuccess else 'Failed') + '\n')
        
        status |= buildSuccess
        
    return status
    
