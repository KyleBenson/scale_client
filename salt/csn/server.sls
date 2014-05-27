WebOb:
  pip.installed

Paste:
  pip.installed

webapp2:
  pip.installed

#TODO: determine if the client needs this too?
protobuf:
  pkg.installed:
    - name: python-protobuf
    - require:
      # not actually sure these are required...
      - pip: WebOb
      - pip: Paste
      - pip: webapp2

