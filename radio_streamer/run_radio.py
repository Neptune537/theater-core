import os, subprocess, sys
os.environ['STREAM_PORT'] = '8082'
py = r'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe'
script = r'C:\Users\blue-\projects\theater\radio_streamer\stream_server.py'
os.chdir(r'C:\Users\blue-\projects\theater')
subprocess.run([py, script])
