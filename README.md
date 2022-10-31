# auto-job-apply
Steps to Install.

### Installation Steps:
    1. pip install -r requirements-win.txt (For win32).
    2. pip install -r requirements.txt ( For linux)

#### Convert UI file to Python File
    1. pytuic5 -x file.ui -o file.py
    x = executable o = output

#### Important Files

_LI.ui_
> GUI File

_main.py_
> entrypoint

_config.yaml_
> for providing args when code run in NON-GUI mode

_output.csv_
> Saves to jobs applied data

_TODO_
>Tasks pending and done

_gitignore_
> adds files to be ignored for commiting