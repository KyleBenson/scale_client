class Publisher:
	def __init__(self):
		pass

	def connect(self):
		raise NotImplementedError()

	def send(self, event):
		raise NotImplementedError()