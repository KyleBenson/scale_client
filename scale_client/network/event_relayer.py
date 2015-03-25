import socket   

class EventRelayer():
	def __init__(self):
                return

        def send(self, remote_clients, remote_port, data):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
		for remote_client in remote_clients:
		sock.sendto(data, (remote_client, remote_port))


	def receive(self, remote_port):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
		# Listen to traffic from every host on port 2800
		sock.bind(('0.0.0.0', self.remote_port))

		while True:
    			data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			print "received message:", data
