hidapi_deps:
  pkg.installed:
    - pkgs:
      - libudev-dev
      - libusb-1.0-0-dev
      - libfox-1.6-dev

tempered:
  pkg.installed:
    - sources: 
      - hidapi: salt://tempered/hidapi_0.8.0-rc1-1_armel.deb
      - hidapi-dev: salt://tempered/hidapi-dev_0.8.0-rc1-1_armel.deb
      - tempered: salt://tempered/tempered_1.0-1_armel.deb
      - tempered-dev: salt://tempered/tempered-dev_1.0-1_armel.deb
  require:
    - pkg: hidapi_deps

