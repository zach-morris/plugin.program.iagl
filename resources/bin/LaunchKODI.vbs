WScript.Sleep(1500)
On Error Resume Next
KodiPath="""" & wscript.arguments(0) & """"
KodiParams=wscript.arguments(1)

Dim objShell
Set objShell = WScript.CreateObject ("WScript.shell")
objShell.run KodiPath & " " & KodiParams