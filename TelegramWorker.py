from PyQt4 import QtCore
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import UpdateShortMessage
import os

class TelegramWorker(QtCore.QObject):

	# SIGNALS (cannot be in constructor https://stackoverflow.com/questions/2970312/pyqt4-qtcore-pyqtsignal-object-has-no-attribute-connect)

	# sent when new message is available NEED mag self. voor deze dingen? 
	newMessage = QtCore.pyqtSignal(str)
	# sent when telegram setup is complete (verified and partner set)
	setReady = QtCore.pyqtSignal()
	# sent when partner username is needed
	reqPartner = QtCore.pyqtSignal()
	# sent when verification is needed
	reqVerify = QtCore.pyqtSignal()		

	# SETUP

	@QtCore.pyqtSlot(str)
	def setPhone(self,phone):
		self.phone = phone
		self.client.send_code_request(self.phone)

	@QtCore.pyqtSlot(str) 
	def verify(self,code):# TODO check of code wel ok was, geeft deze functie feedback? 
		self.client.sign_in(self.phone, code) # NEED check of code klopt
		self.client.add_update_handler(self.newMessageHandler)
		self.loadPartner()
	
	@QtCore.pyqtSlot(str)
	def setPartner(self,username):
		with open('partner','w') as f:
			f.write(username)
		self.partner = username
		self.setReady.emit()


	# NORMAL OPERATION

	def __init__(self):
		super(self.__class__, self).__init__()
		
	# is not part of constructor because in KatApp constructor it is necessary to first connect the signals after calling this constructor
	@QtCore.pyqtSlot()	
	def initialise(self):
		# api credentials
		apiId = 134734
		apiHash = '88e71c3b86c4958290a5609f73054236'

		self.client = TelegramClient('session', apiId, apiHash) # TODO aanpassen naar iets netjes, readen van file
		self.client.connect()

		# check if session file is valid
		if self.client.is_user_authorized():
			self.client.add_update_handler(self.newMessageHandler)
			self.loadPartner()
		else:
			self.reqVerify.emit()

	def newMessageHandler(self,update):
		if isinstance(update, UpdateShortMessage):
			if not update.out:
				# TODO check update.user_id of dat het wel Baert is
				self.newMessage.emit(update.message)
		
	def loadPartner(self):
		# check if text file exists
		if os.path.isfile('partner'):
			with open('partner', 'r') as f:
				self.partner = f.read().rstrip()
			self.setReady.emit()
		else:
			self.reqPartner.emit()

	@QtCore.pyqtSlot(str)
	def sendMessage(self,message):
		self.client.send_message(self.partner, message)
