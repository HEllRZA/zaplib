import os, json

def setup():
	__ENV_VAR__ = "CONFIGBOX_PATH"

	global PATH
	PATH = os.environ.get(__ENV_VAR__, None)

	if not PATH:
		print "> error: {} not set in environment.".format(__ENV_VAR__)

def _from_json(file):
	result = {}

	if os.path.exists(file):
		with open(file, 'r+') as jsonfile:
			result = json.load(jsonfile)

	return result	

class ConfigBox(object):
	def __init__(self):
		self._configs = {}

		# load configs
		if PATH:
			cfg_dir = os.path.join(PATH, "config")
			cfg_files = [f for f in os.listdir(cfg_dir) if f[-5:] == ".json"]

			for file in cfg_files:
				name = file[:-5]
				path = os.path.join(cfg_dir, file)
				self._configs[name] = ConfigPath(_from_json(path))

	def __getitem__(self, key):
		if key in self._configs:
			return self._configs[key]
		else:
			return None

	def find(self, path, value):
		for name, config in self._configs.iteritems():
			try:
				data = reduce(lambda d,k: d[k], path, config())
			except:
				continue
			else:
				if data == value:
					return config

		return None


class ConfigPath(object):
	def __init__(self, data):
		self._data = data
		self._cache = {}

	def __getattr__(self, key):
		if key in self._cache:
			return self._cache[key]
		elif key in self._data:
			if isinstance(self._data[key], dict):
				path = ConfigPath(self._data[key])
				self._cache[key] = path
				return path
			elif key in self._data:
				return self._data[key]
			else:
				return None

	def __call__(self):
		return self._data

setup()
config = ConfigBox()