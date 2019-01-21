call workon PqaWeb1
@REM TODO: build ProbQA engine and copy the Release versions of its DLLs
python ..\..\PqaWeb\manage.py collectstatic --noinput
@REM we clean the static directory first
DEL /F /S /Q D:\Servers\Web\Django\probqa.com-site\Data\StaticRoot
XCOPY /Y /F /S /I ..\..\..\Data\StaticRoot D:\Servers\Web\Django\probqa.com-site\Data\StaticRoot
@REM we delete the contents of destination directory first
DEL /F /S /Q D:\Servers\Web\Django\probqa.com-site\src\PqaWeb
XCOPY /Y /F /S /I /EXCLUDE:NoDeployment.txt ..\..\PqaWeb D:\Servers\Web\Django\probqa.com-site\src\PqaWeb
