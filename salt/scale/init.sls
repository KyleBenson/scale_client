mosquitto:
  pip.installed

pyserial:
  pip.installed

# we need to ignore SSL verification for some reason, at least on the Sheevaplugs
git_no_ssl:
  cmd.run:
    - name: git config --global http.sslVerify false
    - user: root
    - unless: grep 'sslVerify = false' ~/.gitconfig

scale_repo:
  git.latest:
    - name: https://github.com/KyleBenson/SmartAmericaSensors.git
    - target: /usr/local/scale
    - user: root
    - require:
      - pip: mosquitto
      - pip: pyserial
      - cmd: git_no_ssl

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
