mosquitto:
  pip.installed

pyserial:
  pip.installed

scale_repo:
  git.latest:
    - name: http://github.com/KyleBenson/SmartAmericaSensors.git
    - target: /usr/local/scale
    - user: root
    - require:
      - pip: mosquitto
      - pip: pyserial

install_scale_daemon:
  cmd.wait:
    - name: cp /usr/local/scale/scale_client/scale /etc/init.d/
    - watch:
      - git: scale_repo

scale_daemon:
  service.running:
    - name: scale
    - watch:
      - cmd: install_scale_daemon
    - enable: True
