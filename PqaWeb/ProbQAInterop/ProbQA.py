import os
import ctypes

# Initialization and C wrapper follow: please, don't use them in Python code.
# Instead, please use OOP wrapper that follows later.

# Taken from https://stackoverflow.com/questions/7586504/python-accessing-dll-using-ctypes
if os.name == 'nt':
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    def check_bool(result, func, args):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return args

    kernel32.LoadLibraryExW.errcheck = check_bool
    kernel32.LoadLibraryExW.restype = wintypes.HMODULE
    kernel32.LoadLibraryExW.argtypes = (wintypes.LPCWSTR,
                                        wintypes.HANDLE,
                                        wintypes.DWORD)

# CDLL vs WinDLL: https://ammous88.wordpress.com/2014/12/31/ctypes-cdll-vs-windll/
class CDLLEx(ctypes.CDLL):
    def __init__(self, name, mode=0, handle=None, 
                 use_errno=True, use_last_error=False):
        if os.name == 'nt' and handle is None:
            handle = kernel32.LoadLibraryExW(name, None, mode)
        super(CDLLEx, self).__init__(name, mode, handle,
                                     use_errno, use_last_error)

class WinDLLEx(ctypes.WinDLL):
    def __init__(self, name, mode=0, handle=None, 
                 use_errno=False, use_last_error=True):
        if os.name == 'nt' and handle is None:
            handle = kernel32.LoadLibraryExW(name, None, mode)
        super(WinDLLEx, self).__init__(name, mode, handle,
                                       use_errno, use_last_error)

DONT_RESOLVE_DLL_REFERENCES         = 0x00000001
LOAD_LIBRARY_AS_DATAFILE            = 0x00000002
LOAD_WITH_ALTERED_SEARCH_PATH       = 0x00000008
LOAD_IGNORE_CODE_AUTHZ_LEVEL        = 0x00000010  # NT 6.1
LOAD_LIBRARY_AS_IMAGE_RESOURCE      = 0x00000020  # NT 6.0
LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE  = 0x00000040  # NT 6.0

# These cannot be combined with LOAD_WITH_ALTERED_SEARCH_PATH.
# Install update KB2533623 for NT 6.0 & 6.1.
LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR    = 0x00000100
LOAD_LIBRARY_SEARCH_APPLICATION_DIR = 0x00000200
LOAD_LIBRARY_SEARCH_USER_DIRS       = 0x00000400
LOAD_LIBRARY_SEARCH_SYSTEM32        = 0x00000800
LOAD_LIBRARY_SEARCH_DEFAULT_DIRS    = 0x00001000

#TODO: on Linux that would be a .so, but the engine doesn't yet support Linux
pqa_engine_path = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "DLLs/PqaCore.dll"))
print('Initializing engine from:', pqa_engine_path)
pqa_core = CDLLEx(pqa_engine_path, LOAD_WITH_ALTERED_SEARCH_PATH)

# See https://github.com/srogatch/ProbQA/blob/master/ProbQA/PqaCore/Interface/PqaCInterop.h
class CiEngineDefinition(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ('nAnswers', ctypes.c_int64),
        ('nQuestions', ctypes.c_int64),
        ('nTargets', ctypes.c_int64),
        ('precType', ctypes.c_uint8),
        ('precExponent', ctypes.c_uint16),
        ('precMantissa', ctypes.c_uint32),
        ('initAmount', ctypes.c_double),
        ('_memPoolMaxBytes', ctypes.c_uint64),
    ]

class CiAnsweredQuestion(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ('iQuestion', ctypes.c_int64),
        ('iAnswer', ctypes.c_int64),
    ]

class CiEngineDimensions(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ('nAnswers', ctypes.c_int64),
        ('nQuestions', ctypes.c_int64),
        ('nTargets', ctypes.c_int64),
    ]

class CiRatedTarget(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ('iTarget', ctypes.c_int64),
        ('prob', ctypes.c_double),
    ]

# PQACORE_API uint8_t CiLogger_Init(void **ppStrErr, const char* baseName);
pqa_core.CiLogger_Init.restype = ctypes.c_uint8
pqa_core.CiLogger_Init.argtypes = (ctypes.POINTER(ctypes.c_char_p), ctypes.c_char_p)

# PQACORE_API void CiReleaseString(void *pvString);
pqa_core.CiReleaseString.restype = None
pqa_core.CiReleaseString.argtypes = (ctypes.c_char_p,)

# PQACORE_API void* CiPqaGetEngineFactory();
# PQACORE_API void* CiPqaEngineFactory_CreateCpuEngine(void* pvFactory, void **ppError, CiEngineDefinition *pEngDef);
# PQACORE_API void* CiqaEngineFactory_LoadCpuEngine(void *pvFactory, void **ppError, const char* filePath,
#   uint64_t memPoolMaxBytes);

# PQACORE_API void CiReleasePqaError(void *pvErr);
# PQACORE_API void* CiPqaError_ToString(void *pvError, const uint8_t withParams);

# PQACORE_API void CiReleasePqaEngine(void *pvEngine);
# PQACORE_API void* PqaEngine_Train(void *pvEngine, int64_t nQuestions, const CiAnsweredQuestion* const pAQs,
#   const int64_t iTarget, const double amount = 1.0);
# PQACORE_API uint8_t PqaEngine_QuestionPermFromComp(void *pvEngine, const int64_t count, int64_t *pIds);
# PQACORE_API uint8_t PqaEngine_QuestionCompFromPerm(void *pvEngine, const int64_t count, int64_t *pIds);
# PQACORE_API uint8_t PqaEngine_TargetPermFromComp(void *pvEngine, const int64_t count, int64_t *pIds);
# PQACORE_API uint8_t PqaEngine_TargetCompFromPerm(void *pvEngine, const int64_t count, int64_t *pIds);
# PQACORE_API uint64_t PqaEngine_GetTotalQuestionsAsked(void *pvEngine, void **ppError);
# PQACORE_API uint8_t PqaEngine_CopyDims(void *pvEngine, CiEngineDimensions *pDims);
# PQACORE_API int64_t PqaEngine_StartQuiz(void *pvEngine, void **ppError);
# PQACORE_API int64_t PqaEngine_ResumeQuiz(void *pvEngine, void **ppError, const int64_t nAnswered,
#   const CiAnsweredQuestion* const pAQs);
# PQACORE_API int64_t PqaEngine_NextQuestion(void *pvEngine, void **ppError, const int64_t iQuiz);
# PQACORE_API void* PqaEngine_RecordAnswer(void *pvEngine, const int64_t iQuiz, const int64_t iAnswer);
# PQACORE_API int64_t PqaEngine_GetActiveQuestionId(void *pvEngine, void **ppError, const int64_t iQuiz);
# PQACORE_API int64_t PqaEngine_ListTopTargets(void *pvEngine, void **ppError, const int64_t iQuiz,
#   const int64_t maxCount, CiRatedTarget *pDest);
# PQACORE_API void* PqaEngine_RecordQuizTarget(void *pvEngine, const int64_t iQuiz, const int64_t iTarget,
#   const double amount = 1.0);
# PQACORE_API void* PqaEngine_ReleaseQuiz(void *pvEngine, const int64_t iQuiz);
# PQACORE_API void* PqaEngine_SaveKB(void *pvEngine, const char* const filePath, const uint8_t bDoubleBuffer);

# OOP wrapper follows - please, use these in Python code
class PqaException(Exception):
    pass

class Utils:
    def handle_native_string(c_str : ctypes.c_char_p) -> str:
        ans = c_str.value.decode('ascii')
        pqa_core.CiReleaseString(c_str)
        return ans

class SRLogger:
    def init(base_name : str) -> bool:
        str_err = ctypes.c_char_p()
        ans = (pqa_core.CiLogger_Init(ctypes.byref(str_err), ctypes.c_char_p(base_name.encode('ascii'))) != 0)
        if str_err:
            raise PqaException(Utils.handle_native_string(str_err))

class PqaEngine:
    # Permanent-compact ID mappings follow
    def question_perm_from_comp(ids : list) -> bool:
        # https://stackoverflow.com/questions/37197631/ctypes-reading-modified-array
        pass
