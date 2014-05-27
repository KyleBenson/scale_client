python-pip:
  pkg.installed

RPi.GPIO:
  pip.installed:
    - require:
      - pkg: python-pip
