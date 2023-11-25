import json
import os
import shutil
import sys
import ntpath
import colorama

colorama.init(autoreset=True)


def await_action():
	input('\nPress Enter to exit')


def get_cache_dll_dir_path():
	dir_path = os.path.normpath(os.path.join(os.getcwd(), 'dlls'))
	if not os.path.isdir(dir_path):
		os.mkdir(dir_path)

	return dir_path

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


def get_changed_dlls(directory_list):
	for directory in directory_list:
		print('Searching for dll inside {0}'.format(directory))

		directory_path, dll = get_dll_directory(directory)

		if directory_path is None or dll is None:
			print(f'{colorama.Fore.RED}Failed to find bin directory at {0}'.format(directory))
			await_action()
			sys.exit(0)

		print('Bin directory found at: {0}'.format(directory_path))

		if dll in naming_exceptions:
			dll = naming_exceptions[dll]

		print('Target dll file: {0}'.format(dll))

		get_dll_pdb_pair(directory_path + '\\bin', dll)


def print_debug(message):
	if is_debug:
		print(message)


config_file = open('config.json')
config = json.load(config_file)

naming_exceptions = config['Exceptions']

repository_path = config['RepositoryFilePath']
destination_paths = config['DestinationFilepaths']

read_from_dll_folder = config['ReadFromDllFolder']
write_to_dll_folder = config['WriteCopiesToDllFolder']

is_debug = config['EnableDebug']
	
print()
print('Repository path: {0}'.format(repository_path))
print('Destination paths: {0}'.format(destination_paths))

dll_paths = []

if read_from_dll_folder:
	for f in os.listdir(get_cache_dll_dir_path()):
		if f.split('.')[-1] == 'dll':
			dll_paths.append(os.path.normpath(os.path.join(get_cache_dll_dir_path(), f)))
else:
	from git import Repo
	
	repo = Repo(repository_path)
	changed_files = [item.a_path for item in repo.index.diff(None)]

	print('Changed files:')
	for file in changed_files:
		print(file)

	dir_list = [x.removesuffix(x.split('/')[-1]) for x in changed_files]

	print('List of init directories: ', dir_list)

	get_changed_dlls(dir_list)

dll_paths = list(dict.fromkeys(dll_paths))
dlls = [x.split('\\')[-1] for x in dll_paths]

pdb_paths = [x.split('.dll')[0] + '.pdb' for x in dll_paths]
pdbs = [x.split('.dll')[0] + '.pdb' for x in dlls]

print('Dll found paths:')
for path in dll_paths:
	print(path)

print(f'\n{colorama.Fore.CYAN}Dlls found:')
for dll in dlls:
	print(f'{colorama.Fore.CYAN}Dll: {dll}')

if write_to_dll_folder:
	cache_dll_folder = get_cache_dll_dir_path()
	for dll_path in dll_paths:
		if dll_path != cache_dll_folder:
			shutil.copy(dll_path, cache_dll_folder)
	for pdb_path in pdb_paths:
		if pdb_path != cache_dll_folder:
			shutil.copy(pdb_path, cache_dll_folder)

try:
	for destination_path in destination_paths:
		print(f'{colorama.Fore.CYAN}Moving to: {destination_path}')

		for i in range(len(dll_paths)):
			for dest in search_file(dlls[i], destination_path):
				dest_clear = dest.removesuffix(dlls[i])

				print_debug('Moving {0} to {1}'.format(dll_paths[i], dest_clear + dlls[i]))
				shutil.copy(dll_paths[i], dest_clear + dlls[i])

				print_debug('Moving {0} to {1}'.format(pdb_paths[i], dest_clear + pdbs[i]))
				shutil.copy(dll_paths[i], dest_clear + pdbs[i])

	await_action()

except Exception as e:
	print(f'{colorama.Fore.RED}Exception has occurred:', e)
	await_action()

