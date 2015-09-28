import sublime_plugin, sublime, sys, os, json, socketserver, socket
from sublime import Region

from functools import partial
from threading import Thread

from GulpServer.Utils import ignore, parse_messages
from GulpServer.Settings import Settings
from GulpServer.Logging import Console




END_OF_MESSAGE = b'\n'[0]
HOST = '127.0.0.1'
PORT = 30048




on_received_callbacks = []




# Add a callback when data is received
def on_received(callback):
	""" Add a callback to the server's on_receive event """
	global on_received_callbacks
	on_received_callbacks = [callback]
	# on_received_callbacks.append(callback)




class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	def __init__(self, server_address, RequestHandlerClass):
		socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)
		self.clients = []

	def add_client(self, client):
		server.clients.append(client)

	def remove_client(self, client):
		if client in self.clients:
			self.clients.remove(client)

	def send_all(self, data):
		""" Send data to all clients """
		for client in self.clients:
			client.send(data)

	def send(self, data, id_name):
		""" Send data to a specific client """
		for client in self.clients:
			if client.id == id_name:
				client.send(data)

	def close_requests(self):
		""" Close all requests of the server """
		for client in self.clients:
			client.finish()
		self.clients = []




class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
	""" Server request handler """
	encoding = 'UTF-8'

	def handshake(self):
		data_bytes = self.recvall()
		handshake = json.loads(data_bytes.decode(self.encoding))

		if handshake.get('id'):
			self.id = handshake['id']
			self.server.add_client(self)
			console.log('"{0}"'.format(self.id), 'connected', '- Total number connections:', len(self.server.clients))
			self.send({ "handshake": "hello" })

			return True
		else:
			return False

	def handle(self):
		self.should_receieve = True
		self.closed = False

		with ignore(Exception, origin="ThreadedTCPRequestHandler.handle"):
			if not self.handshake():
				return self.finish()

			while self.should_receieve:
				data_bytes = self.recvall()

				if not data_bytes:
					break

				# Sockets may queue messages and send them as a single message
				# In order to get each JSON object separately, data_bytes must be
				# converted to a string and split by END_OF_MESSAGE. The parse_messages
				# function will do that and will also run json.loads on each string
				messages = parse_messages(data_bytes)

				for message in messages:
					for callback in on_received_callbacks:
						with ignore(Exception, origin="ThreadedTCPRequestHandler.handle"):
							callback(message)

	def finish(self):
		""" Tie up any loose ends with the request """
		# If the client has not been closed for some reason, close it
		if not self.closed:
			self.request.close()

		# Remove self from list of server clients
		self.server.remove_client(self)
		self.closed = True

		# if not hasattr(self, 'id'):
		# 	return console.log('Disconnected', '- Total number of connections', len(self.server.clients))

		console.log('"{0}"'.format(getattr(self, 'id', 'Unknown')), 'disconnected', '- Total number of connections', len(self.server.clients))

	def send(self, data):
		# Send data to the client
		with ignore(Exception, origin='ThreadedTCPRequestHandler.send'):
			data = sublime.encode_value(data)
			self.request.sendall((data).encode(self.encoding))
			return

		self.finish()
		print('finish after send')

	# Keep receiving until an END_OF_MESSAGE is hit.
	def recvall(self, buffer_size=4096):
		try:
			data_bytes = self.request.recv(buffer_size)

			if not data_bytes:
				return data_bytes

			# Keep receiving until the end of message is hit
			while data_bytes[-1] != END_OF_MESSAGE:
				data_bytes += self.request.recv(buffer_size)

		except Exception as ex:
			console.log('Receiving error', ex)
			return b''

		return data_bytes




server = None
server_thread = None




def start_server():
	""" Start the server """
	global server, server_thread

	if server != None:
		return console.log('Server is already running')

	server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
	server_thread = Thread(target=server.serve_forever, daemon=True)
	server_thread.start()
	console.log('Server started')

def stop_server():
	""" Stop the server """
	global server

	if server == None:
		return console.log('Server is already shutdown')

	server.close_requests()
	server.shutdown()
	server = None
	server_thread = None
	console.log('Server stopped')




class StartServerCommand(sublime_plugin.ApplicationCommand):
	""" Start the server """
	def run(self):
		sublime.set_timeout_async(start_server, 2000)

	def is_enabled(self):
		return server == None and server_thread != None and not server_thread.is_alive()

class StopServerCommand(sublime_plugin.ApplicationCommand):
	""" Stop the server """
	def run(self):
		stop_server()

	def is_enabled(self):
		return server != None and server_thread != None and server_thread.is_alive()




user_settings = None
console = None




def plugin_loaded():
	# Setting a timeout will ensure the socket is clear for reuse
	sublime.set_timeout_async(start_server, 2000)
	global PORT, user_settings, console
	console = Console()
	user_settings = Settings()
	PORT = user_settings.get('port')




def plugin_unloaded():
	stop_server()