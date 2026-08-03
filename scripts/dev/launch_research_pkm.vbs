Set objShell = CreateObject("Wscript.Shell")
objShell.CurrentDirectory = "D:\Quan_ly_kien_thuc"
cmd = """D:\Quan_ly_kien_thuc\.venv\Scripts\python.exe"" ""D:\Quan_ly_kien_thuc\main.py"""
objShell.Run cmd, 0, False
