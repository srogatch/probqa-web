from __future__ import annotations
import os
import ctypes
from enum import Enum
from typing import List, Tuple

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

# TODO: on Linux that would be a .so, but the engine doesn't yet support Linux
pqa_engine_path = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DLLs/PqaCore.dll'))
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
        ('memPoolMaxBytes', ctypes.c_uint64),
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


# PQACORE_API uint8_t Logger_Init(void **ppStrErr, const char* baseName);
pqa_core.Logger_Init.restype = ctypes.c_uint8
pqa_core.Logger_Init.argtypes = (ctypes.POINTER(ctypes.c_char_p), ctypes.c_char_p)

# PQACORE_API void CiReleaseString(void *pvString);
pqa_core.CiReleaseString.restype = None
pqa_core.CiReleaseString.argtypes = (ctypes.c_char_p,)

# PQACORE_API void* CiGetPqaEngineFactory();
pqa_core.CiGetPqaEngineFactory.restype = ctypes.c_void_p
pqa_core.CiGetPqaEngineFactory.argtypes = None

# PQACORE_API void* PqaEngineFactory_CreateCpuEngine(void* pvFactory, void **ppError,
#     const CiEngineDefinition *pEngDef);
pqa_core.PqaEngineFactory_CreateCpuEngine.restype = ctypes.c_void_p
pqa_core.PqaEngineFactory_CreateCpuEngine.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
    ctypes.POINTER(CiEngineDefinition))

# PQACORE_API void* PqaEngineFactory_LoadCpuEngine(void *pvFactory, void **ppError, const char* filePath,
#   uint64_t memPoolMaxBytes);
pqa_core.PqaEngineFactory_LoadCpuEngine.restype = ctypes.c_void_p  # C Engine
pqa_core.PqaEngineFactory_LoadCpuEngine.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_char_p, ctypes.c_uint64)

# PQACORE_API void CiReleasePqaError(void *pvErr);
pqa_core.CiReleasePqaError.restype = None
pqa_core.CiReleasePqaError.argtypes = (ctypes.c_void_p,)

# PQACORE_API void* PqaError_ToString(void *pvError, const uint8_t withParams);
# restype has to be c_void_p to workaround this problem:
# https://stackoverflow.com/questions/53999442/inconsistent-c-char-p-behavior-between-returning-vs-pointer-assignment
pqa_core.PqaError_ToString.restype = ctypes.c_void_p
pqa_core.PqaError_ToString.argtypes = (ctypes.c_void_p, ctypes.c_bool)

# PQACORE_API void CiReleasePqaEngine(void *pvEngine);
pqa_core.CiReleasePqaEngine.restype = None
pqa_core.CiReleasePqaEngine.argtypes = (ctypes.c_void_p,)

# PQACORE_API void* PqaEngine_Train(void *pvEngine, int64_t nQuestions, const CiAnsweredQuestion* const pAQs,
#   const int64_t iTarget, const double amount = 1.0);
pqa_core.PqaEngine_Train.restype = ctypes.c_void_p # The error
pqa_core.PqaEngine_Train.argtypes = (ctypes.c_void_p, ctypes.c_int64, ctypes.POINTER(CiAnsweredQuestion),
    ctypes.c_int64, ctypes.c_double)

# PQACORE_API uint8_t PqaEngine_QuestionPermFromComp(void *pvEngine, const int64_t count, int64_t *pIds);
pqa_core.PqaEngine_QuestionPermFromComp.restype = ctypes.c_bool
pqa_core.PqaEngine_QuestionPermFromComp.argtypes = (ctypes.c_void_p, ctypes.c_int64, ctypes.POINTER(ctypes.c_int64))

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
    @staticmethod
    def handle_native_string(c_str : ctypes.c_char_p) -> str:
        ans = c_str.value.decode('ascii')
        pqa_core.CiReleaseString(c_str)
        return ans

    @staticmethod
    def str_to_c_char_p(s : str) -> ctypes.c_char_p:
        return ctypes.c_char_p(s.encode('ascii'))


class SRLogger:
    @staticmethod
    def init(base_name : str) -> bool:
        str_err = ctypes.c_char_p()
        ans = (pqa_core.Logger_Init(ctypes.byref(str_err), Utils.str_to_c_char_p(base_name)) != 0)
        if str_err:
            raise PqaException(Utils.handle_native_string(str_err))
        return ans


class PrecisionType(Enum):
    NONE = 0
    FLOAT = 1
    FLOAT_PAIR = 2
    DOUBLE = 3
    DOUBLE_PAIR = 4
    ARBITRARY = 5


class AnsweredQuestion:
    def __init__(self, i_question, i_answer):
        self.i_question = i_question
        self.i_answer = i_answer


class EngineDefinition:
    DEFAULT_MEM_POOL_MAX_BYTES = 512 * 1024 * 1024
    def __init__(self, n_answers : int, n_questions : int, n_targets : int, init_amount = 1.0,
                 prec_type = PrecisionType.DOUBLE, prec_exponent = 11, prec_mantissa = 53,
                 mem_pool_max_bytes = DEFAULT_MEM_POOL_MAX_BYTES):
        self.n_answers = n_answers
        self.n_questions = n_questions
        self.n_targets = n_targets
        self.init_amount = init_amount
        self.prec_type = prec_type
        self.prec_exponent = prec_exponent
        self.prec_mantissa = prec_mantissa
        self.mem_pool_max_bytes = mem_pool_max_bytes


class PqaError:
    @staticmethod
    def factor(c_err: ctypes.c_void_p) -> PqaError:
        if (c_err.value is None) or (c_err.value == 0):
            return None
        return PqaError(c_err)
    
    def __init__(self, c_err : ctypes.c_void_p):
        self.c_err = c_err
    
    def __del__(self):
        pqa_core.CiReleasePqaError(self.c_err)
        
    def __str__(self):
        return self.to_string(True)
        
    def to_string(self, with_params : bool) -> str:
        if (self.c_err.value is None) or (self.c_err.value == 0):
            return 'Success'
        void_ptr = ctypes.c_void_p()
        void_ptr.value = pqa_core.PqaError_ToString(self.c_err, ctypes.c_bool(with_params))
        return Utils.handle_native_string(ctypes.cast(void_ptr, ctypes.c_char_p))
    

class PqaEngine:
    def __init__(self, c_engine : ctypes.c_void_p):
        self.c_engine = c_engine
    
    def __del__(self):
        pqa_core.CiReleasePqaEngine(self.c_engine)

    # Permanent-compact ID mappings follow
    def question_perm_from_comp(self, ids: List[int]) -> List[int]:
        # https://stackoverflow.com/questions/37197631/ctypes-reading-modified-array
        n_ids = len(ids)
        array_type = ctypes.c_int64 * n_ids
        c_ids = array_type(*ids)
        b_ok = pqa_core.PqaEngine_QuestionPermFromComp(self.c_engine, ctypes.c_int64(n_ids), c_ids)
        if not b_ok:
            raise PqaException("Failed computing permanent from compact IDs.")
        return list(c_ids)

    def train(self, answered_questions: List[AnsweredQuestion], i_target : int,
              amount : float = 1.0):
        n_questions = len(answered_questions)
        c_aqs = CiAnsweredQuestion * n_questions
        for i in range(n_questions):
            c_aqs[i].iQuestion = answered_questions[i].i_question
            c_aqs[i].iAnswer = answered_questions[i].i_answer
        return PqaError.factor(pqa_core.PqaEngine_Train(
            self.c_engine, ctypes.c_int64(n_questions), ctypes.byref(c_aqs),
            ctypes.c_int64(i_target), ctypes.c_double(amount)
        ))


class PqaEngineFactory:
    instance = None
    
    def __init__(self):
        self.c_factory = pqa_core.CiGetPqaEngineFactory()

    def create_cpu_engine(self, eng_def : EngineDefinition) -> Tuple[PqaEngine, PqaError]:
        c_err = ctypes.c_void_p()
        c_eng_def = CiEngineDefinition()
        c_eng_def.nAnswers = eng_def.n_answers
        c_eng_def.nQuestions = eng_def.n_questions
        c_eng_def.nTargets = eng_def.n_targets
        c_eng_def.precType = eng_def.prec_type.value
        c_eng_def.precExponent = eng_def.prec_exponent
        c_eng_def.precMantissa = eng_def.prec_mantissa
        c_eng_def.initAmount = eng_def.init_amount
        c_eng_def.mem_pool_max_bytes = eng_def.mem_pool_max_bytes
        c_engine = ctypes.c_void_p()
        try:
            # If an exception is thrown from C++ code, then we can safely assume no engine is returned
            c_engine.value = pqa_core.PqaEngineFactory_CreateCpuEngine(self.c_factory, ctypes.byref(c_err),
                ctypes.byref(c_eng_def))
        finally:
            err = PqaError.factor(c_err)
        if (c_engine.value is None) or (c_engine.value == 0):
            raise PqaException('Couldn\'t create a CPU Engine due to a native error: ' + str(err))
        return (PqaEngine(c_engine), err)

    def load_cpu_engine(self, file_path:str, mem_pool_max_bytes:int = EngineDefinition.DEFAULT_MEM_POOL_MAX_BYTES
                        ) -> Tuple[PqaEngine, PqaError]:
        c_err = ctypes.c_void_p()
        c_engine = ctypes.c_void_p()
        try:
            c_engine.value = pqa_core.PqaEngineFactory_LoadCpuEngine(self.c_factory, ctypes.byref(c_err),
                Utils.str_to_c_char_p(file_path), ctypes.c_uint64(mem_pool_max_bytes))
        finally:
            err = PqaError.factor(c_err)
        if (c_engine.value is None) or (c_engine.value == 0):
            raise PqaException('Couldn\'t load a CPU Engine due to a native error: ' + str(err))
        return (PqaEngine(c_engine), err)

PqaEngineFactory.instance = PqaEngineFactory()
