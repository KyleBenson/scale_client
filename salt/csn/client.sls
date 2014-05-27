libssl0.9.8:
  pkg.installed:
    - sources:
      #TODO: get this from an actual repo to keep updated
      - libssl0.9.8: salt://csn/libssl0.9.8_0.9.8o-4squeeze14_armel.deb

/usr/sbin/csnd:
  file.managed:
    - source: salt://csn/usr/sbin/csnd
    - mode: 0755

/usr/bin/csn-config:
  file.managed:
    - source: salt://csn/usr/bin/csn-config
    - mode: 0755

/etc/init.d/csnd:
  file.managed:
    - source: salt://csn/etc/init.d/csnd
    - mode: 0755

#TODO: get location info from somewhere, maybe a grain?
csn-set-location:
  cmd.wait:
    - name: csn-config set-location 34.13834 -118.12443 1
    #TODO: figure out robust way of making sure this stays updated, cmd.wait and watch some file?
    - watch:
      - service: csnd
      #- unless: grep location /etc/CSNClientSettings

csn-set-name:
  cmd.wait:
    #TODO: get name from hostname
    - name: csn-config set-name SCALE
    - watch:
      - cmd: csn-set-location

csnd:
  service.running:
    - require:
      - file: /usr/sbin/csnd
      - file: /usr/bin/csn-config
      - file: /etc/init.d/csnd
      - pkg: libssl0.9.8
      # these aren't actually required here, could move elsewhere for the server...
      - pip: webapp2
      - pip: Paste
      - pip: WebOb
    - enable: True
