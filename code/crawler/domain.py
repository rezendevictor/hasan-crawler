from datetime import datetime, timedelta

class Domain():

	def __init__(self,nam_domain: str,int_time_limit_between_requests: int):
		''' 
			Classe para definição dos dominios de acessibilidade das URL
			:parram - nam_domain : String com o nome do dominio (URL sem path)
					- int_time_between_requests : Tempo limite para operação de requisição
		'''

		self.time_last_access = datetime(1970,1,1)
		self.nam_domain = nam_domain
		self.int_time_limit_seconds  = int_time_limit_between_requests

	@property
	def time_since_last_access(self) -> int:		
		''' 
			Metodo que retorna o tempo passado des do ultimo acesso
			:parram - None
			:return - Tempo em segundos
		'''

		return datetime.now() - self.time_last_access

	def accessed_now(self):
		'''
			Metodo que define o acesso do Domain. Captura o tempo atual
		'''

		self.time_last_access = datetime.now()

	def is_accessible(self) -> bool:
		''' 
			Metodo para retornar o estado da acessibilidade
			:parram - None
			:return - Boolean com a resposta de possibilidade de acessibilidade do dominio (True/False)		
		'''		

		seconds = timedelta(seconds=10)		
		if self.time_since_last_access <= seconds:
			return False
		return True

	def __hash__(self):
		return hash(self.nam_domain)

	def __eq__(self, domain):
		return self.nam_domain == domain

	def __str__(self):
		return self.nam_domain

	def __repr__(self):
		return str(self)
