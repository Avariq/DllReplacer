import json
import os
import shutil
import sys
import ntpath

from git import Repo


def await_action():
	input('Press Enter to exit')


def search_file(filename, directory):
	res = []

	for dirpath, dirnames, filenames in os.walk(directory):
		for file_name in [f for f in filenames]:
			if file_name == filename:
				res.append(os.path.normpath(os.path.join(dirpath, file_name)))

	return res


def get_dll_directory(directory):
	curr_dir = directory

	for i in range(len(curr_dir.split('/'))):
		curr = os.path.join(repository_path, curr_dir)
		for file_name in os.listdir(curr):
			if file_name == 'bin':
				return os.path.normpath(os.path.join(repository_path, curr_dir)), ntpath.basename(os.path.normpath(curr_dir))

		curr_dir = curr_dir[:-(len(curr_dir.split('/')[-1]) + 1)]

	return None, None


def get_dll_pdb_pair(directory, dll_file_name):
	dll_file_name = os.path.normpath(dll_file_name)

	target_file = dll_file_name + '.dll'

	print('Searching for dll {0} and its corresponding pdb inside directory {1}'.format(target_file, directory))

	for dirpath, dirnames, filenames in os.walk(directory):
		for file_name in [f for f in filenames]:
			print('Searching...', os.path.join(dirpath, file_name))

			if file_name == target_file:
				dll_paths.append(os.path.normpath(os.path.join(dirpath, file_name)))


config_file = open('config.json')
config = json.load(config_file)

naming_exceptions = config['Exceptions']

repository_path = config['RepositoryFilePath']
destination_path = config['DestinationFilepath']

repo = Repo(config['RepositoryFilePath'])
changed_files = [item.a_path for item in repo.index.diff(None)]

print('Changed files:')
for file in changed_files:
	print(file)
print()
print('Repository path: {0}'.format(repository_path))
print('Destination path: {0}'.format(destination_path))

dir_list = [x.removesuffix(x.split('/')[-1]) for x in changed_files]

print('List of init directories: ', dir_list)

dll_paths = []

for directory in dir_list:
	print('Searching for dll inside {0}'.format(directory))

	directory_path, dll = get_dll_directory(directory)

	if directory_path is None or dll is None:
		print('Failed to find bin directory at {0}'.format(directory))
		await_action()
		sys.exit(0)

	print('Bin directory found at: {0}'.format(directory_path))

	if dll in naming_exceptions:
		dll = naming_exceptions[dll]

	print('Target dll file: {0}'.format(dll))

	get_dll_pdb_pair(directory_path + '\\bin', dll)

dll_paths = list(dict.fromkeys(dll_paths))
dlls = [x.split('\\')[-1] for x in dll_paths]

pdb_paths = [x.split('.dll')[0] + '.pdb' for x in dll_paths]
pdbs = [x.split('.dll')[0] + '.pdb' for x in dlls]

print('Dll found paths:')
for path in dll_paths:
	print(path)

print('Dlls found:')
for dll in dlls:
	print('Dll: {0}'.format(dll))

try:
	for i in range(len(dll_paths)):
		for dest in search_file(dlls[i], destination_path):
			dest_clear = dest.removesuffix(dlls[i])

			print('Moving {0} to {1}'.format(dll_paths[i], dest_clear + dlls[i]))
			shutil.copy(dll_paths[i], dest_clear + dlls[i])

			print('Moving {0} to {1}'.format(pdb_paths[i], dest_clear + pdbs[i]))
			shutil.copy(dll_paths[i], dest_clear + pdbs[i])

	await_action()

except Exception as e:
	print('Exception has occurred:', e)
	await_action()

