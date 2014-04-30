from __future__ import print_function
import subprocess, re

cmd = '/root/SmartAmericaSensors/temperature/temperature-streams'
result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#NOTE: we assume the temperature is in Celsius and don't scan for the degree symbol
exp = re.compile(r'Device ([^:]*): Sensor ([0-9]*): Temperature: ([0-9\.]*)')

#NOTE: for line in result.stdout doesn't do "real-time" updates in Py2
for line in iter(result.stdout.readline, ''):
    match = exp.match(line)
    try:
        temperature = float(match.group(3))
    except AttributeError as e:
        print('Error parsing temperature: %s' % e)
        continue
    print(u'%.2f\N{DEGREE SIGN}C' % temperature)
    if temperature > 24:
        print("ALARM: temp > 24!!!")
