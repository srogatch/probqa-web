@REM This assumes a virutal environment is created with name PqaWeb1
call workon PqaWeb1
@REM Change to Release when you don't need to debug the engine
SET Configuration=Debug
FOR %%e in (dll pdb) DO (
  FOR %%n in (PqaCore SRPlatform) DO (
    @REM This assumes the relative path to ProbQA engine
    XCOPY /Y /F ..\..\..\..\ProbQA\ProbQA\x64\%Configuration%\%%n.%%e .\ProbQAInterop\DLLs\
  )
)
python manage.py runserver
REM pause
