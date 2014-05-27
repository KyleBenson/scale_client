python-pip:
  pkg.installed

WebOb:
  pip.installed:
    - require:
      - pkg: python-pip

Paste:
  pip.installed:
    - require:
      - pkg: python-pip

webapp2:
  pip.installed:
    - require:
      - pkg: python-pip

#TODO: determine if the client needs this too?
protobuf:
  pkg.installed:
    - name: python-protobuf
    - require:
      # not actually sure these are required...
      - pip: WebOb
      - pip: Paste
      - pip: webapp2

