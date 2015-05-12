import sublime_plugin, sublime, sys, os
from sublime import Region
from functools import partial
from Server.Utils import all_of_type




def is_possible_value(setting, possible_values):
	if isinstance(setting, list):
		return all([value in possible_values for value in setting])

	elif isinstance(setting, dict):
		return all([value in possible_values for value in setting.values()])

	else:
		return setting in possible_values




class Settings(object):
	""" A wrapper for a sublime.Settings object """
	# The sublime.Settings object
	loaded_settings = None
	settings = {}

	# Default settings will be used where no user settings have been defined 
	# name, default value, list of possible values
	default_settings = {
		"trim_empty_lines": (False, None),
		"character_count": (32, None)
	}

	# Case sensitive 
	settings_basename = 'Customizations.sublime-settings'

	def load(self):
		self.loaded_settings = sublime.load_settings(self.settings_basename)
		self.loaded_settings.clear_on_change('customizations/customizations')
		self.verify()
		self.loaded_settings.add_on_change('customizations/customizations', self.load)

	def save(self):
		sublime.save_settings(self.settings_basename)

	def set(self, key, value):
		""" Set a value into the sublime.Settings object """
		self.load_setting.set(key, value)

	def get(self, key):
		""" Get a value by key from the settings """
		return self.settings[key]


	# Use the default setting if the setting is missing or not a valid value   
	def verify(self):
		""" Verify that the settings are correct """

		loaded_settings = self.loaded_settings

		for setting_name in self.default_settings:
			(default, possible_values) = self.default_settings[setting_name]
			setting = loaded_settings.get(setting_name, None)
			both = [setting, default]
			setting_is_valid = True
			
			self.settings[setting_name] = default

			if setting == None:
				continue

			# print(setting_is_valid, setting_name, setting, default)

			# Check if both are of type bool
			if all_of_type(both, bool):
				pass

			# Check if both are of type int  
			elif all_of_type(both, int):
				pass

			# Check if both are of type str  
			elif all_of_type(both, str):
				pass

			# Check if all list are strings 
			elif all_of_type(both, list) and all_of_type(setting, str):
				pass

			# Check if all dict values are strings 
			elif all_of_type(both, dict) and all_of_type(list(setting.values()), str):
				pass

			# If not, setting is invalid 
			else:
				setting_is_valid = False

			# Check if the value is one of the possible values 
			if (setting_is_valid and possible_values) and not is_possible_value(setting, possible_values):
				setting_is_valid = False

			if setting_is_valid:
				self.settings[setting_name] = setting
			else:
				print('Customizations: You messed up a setting', setting_name, setting, default)

		# print(self.settings)
			






