import subprocess

cmd = 'examples/temperature-streams'
result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
#for line in result.stdout:
#NOTE: for line in result.stdout doesn't do "real-time" updates in Py2
for line in iter(result.stdout.readline, ''):
    print("%s" % line.strip())
