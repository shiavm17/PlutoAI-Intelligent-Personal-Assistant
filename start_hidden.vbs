Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Change working directory to project directory to ensure relative paths resolve correctly
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = scriptDir

' Determine path to pythonw.exe
Dim pythonwPath
If fso.FileExists(".conda\pythonw.exe") Then
    pythonwPath = ".conda\pythonw.exe"
Else
    pythonwPath = "pythonw.exe"
End If

' Run Main.py in background (0 = hide window, False = don't wait for execution to finish)
WshShell.Run pythonwPath & " Main.py", 0, False

' Wait 3 seconds for Main.py to initialize directories/reminders
WScript.Sleep 3000

' Run app.py in background (0 = hide window, False = don't wait for execution to finish)
WshShell.Run pythonwPath & " app.py", 0, False
