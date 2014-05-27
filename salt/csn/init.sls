include:
  - csn.client
  - csn.server

# This is our hack to make the client report to the local 'server'
hosts-hack:
  file.append:
    - name: /etc/hosts
    - text:
      - 127.0.0.1 csn.cacr.caltech.edu

