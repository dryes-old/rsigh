#!/usr/bin/python3

# Author: Joseph Wiseman <joswiseman@gmail>
# URL: https://github.com/dryes/rsigh/
#
# This file is part of rsigh.
#
# rsigh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rsigh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rsigh.  If not, see <http://www.gnu.org/licenses/>.

##rsigh is dedicated to lhbandit and https://www.nzbs.org - thank you.
#really sensitive info goes here

##TODO: fix minimum volume filesize (currently ~10MB), docstrings.

import argparse,configparser,gzip,os,shutil,signal,subprocess,sys,time,uuid
from rsigh.par2 import PAR2
from rsigh.rar import RAR
from rsigh.sqlite import SQLite
from rsigh.truecrypt import TrueCrypt

def handler(signum, frame):
	rmtmp()
	sys.exit(1)

def rmtmp():
	try:
		temp
	except NameError:
		return

	if os.path.isdir(temp):
		try:
			shutil.rmtree(temp)
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])

def init_configparser(filename='~/.config/rsigh/rsigh.cfg'):
	filename = os.path.expanduser(filename)
	if not os.path.isfile(filename):
		if not os.path.isdir(os.path.dirname(filename)):
			try:
				os.makedirs(os.path.dirname(filename))
			except:
				if len(str(sys.exc_info()[1])) > 0:
					print(sys.exc_info()[1])
				sys.exit(1)
		try:
			shutil.copy(os.path.join(os.path.dirname(__file__), 'docs', 'example.cfg'), filename)
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			sys.exit(1)

	config = configparser.ConfigParser()
	config.read(filename)

	return config

def init_argparse(config):
	parser = argparse.ArgumentParser(description='Post encrypted files to Usenet.', usage=os.path.basename(sys.argv[0]) + ' [--opts] input')

	parser.add_argument('input', nargs='?', help='dirname or file to process/search for', default='')

	parser.add_argument('--search', '-s', action='store_true', help='search dirname column', default=False)
	parser.add_argument('--collect', '-c', action='store_true', help='copy NZB to watch dir', default=False)
	parser.add_argument('--dupecheck', action='store_true', help='search for duplicate dirname', default=False)
	parser.add_argument('--list', '-l', action='store_true', help='list last 50 posts', default=False)
	parser.add_argument('--list-old', action='store_true', help='list posts dated > retenton', default=False)
	parser.add_argument('--delete', action='store_true', help='delete files and database row', default=False)	

	parser.add_argument('--post-process', '-p', action='store_true', help='post-process downloaded NZBs', default=False)

	parser.add_argument('--sqlite-db', default=config['sqlite']['database'])
	parser.add_argument('--sqlite-vacuum', '-v', action='store_true', help='vacuum SQLite database and exit', default=False)

	parser.add_argument('--no-par2', action='store_true', help='skip generation of PAR2 files', default=False)
	parser.add_argument('--no-post', action='store_true', help='process files without posting', default=False)

	parser.add_argument('--tch-dir', default=config['store']['tchs'])
	parser.add_argument('--nzb-dir', default=config['store']['nzbs'])
	parser.add_argument('--watch-dir', default=config['directories']['watch'])
	parser.add_argument('--tmp-dir', default=config['directories']['tmp'])

	parser.add_argument('--truecrypt-bin', default=config['binaries']['truecrypt'])
	parser.add_argument('--rar-bin', default=config['binaries']['rar'])
	parser.add_argument('--unrar-bin', default=config['binaries']['unrar'])
	parser.add_argument('--par2-bin', default=config['binaries']['par2'])
	parser.add_argument('--python2-bin', default=config['binaries']['python2'])

	parser.add_argument('--tc-ov-password', default=None)
	parser.add_argument('--tc-hv-password', default=None)
	parser.add_argument('--tc-volume-type', default='hidden')
	parser.add_argument('--tc-encryption-algo', default='AES')
	parser.add_argument('--tc-hash-algo', default='RIPEMD-160')
	parser.add_argument('--tc-filesystem', default='FAT')
	parser.add_argument('--tc-randcharlen', default=6400)

	parser.add_argument('--par2-redundancy', default=config['par']['redundancy'])
	parser.add_argument('--par2-number', default=config['par']['number'])

	parser.add_argument('--nm-script', default=config['newsmangler']['script'])
	parser.add_argument('--nm-group', '-g', default=config['newsmangler']['group'])
	parser.add_argument('--nm-config', default=config['newsmangler']['config'])

	parser.add_argument('--retention', default=config['usenet']['retention'])

	args = parser.parse_args()

	return vars(args)

def init_sqlite(filename='~/.rsigh/rsigh.db'):
	filename = os.path.expanduser(filename)
	if not os.path.isdir(os.path.dirname(filename)):
		try:
			os.makedirs(os.path.dirname(filename))
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			sys.exit(1)

	if not os.path.isfile(filename):
			sqlite = SQLite(filename)
			sqlite.execute('''CREATE TABLE rsigh (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				dirname TEXT UNIQUE NOT NULL,
				volume TEXT UNIQUE NOT NULL,
				ov_password TEXT NOT NULL,
				hv_password TEXT DEFAULT NULL,
				rar_password TEXT DEFAULT NULL,
				posted INT DEFAULT NULL)''')
	else:
		sqlite = SQLite(filename)

	if sqlite == False:
		sys.exit(1)

	return sqlite

def filesize(path):
	filesize = 0
	if os.path.isdir(path):
		for dirpath, dirnames, filenames in os.walk(path):
			for f in filenames:
				filesize += os.path.getsize(os.path.join(dirpath, f))
	elif os.path.isfile(path):
		filesize = os.path.getsize(path)

	return filesize

def filecount(path):
	return len([f for f in os.listdir(path) if os.path.isfile(f)])

def search(sqlite, dirname):
	tuple = ('%' + dirname + '%',)
	res = sqlite.query('''SELECT dirname, posted FROM rsigh WHERE dirname LIKE ? ORDER BY posted DESC''', tuple)
	for r in res:
		print(r)

	return res

def dupecheck(sqlite, input):
	if os.path.isdir(input):
		tuple = (os.path.dirname(input),)
	else:
		tuple = (os.path.basename(input),)

	res = sqlite.query('''SELECT count(*) FROM rsigh WHERE dirname = ? LIMIT 1''', tuple)
	if res[0][0] == 0:
		return True
	else:
		return False

def volcheck(sqlite, filename):
	tuple = (filename,)
	res = sqlite.query('''SELECT count(*) FROM rsigh WHERE volume = ? LIMIT 1''', tuple)
	if res[0][0] == 0:
		return True
	else:
		return False

def list(sqlite, limit=50):
	tuple = (limit,)
	res = sqlite.query('''SELECT dirname, volume, posted FROM rsigh ORDER BY posted DESC LIMIT ?''', tuple)
	for r in res:
		print(r)

	return res

def listold(sqlite, retention, limit=50):
	tuple = ((int(str(time.time()).split('.')[0])-(float(retention*86400))), limit)
	res = sqlite.query('''SELECT dirname, volume, posted FROM rsigh WHERE posted < ? ORDER BY posted ASC LIMIT ?''', tuple)
	for r in res:
		print(r)

	return res

def collect(sqlite, dirname, nzbdir, watchdir):
	tuple = (dirname,)
	res = sqlite.query('''SELECT volume FROM rsigh WHERE dirname = ? LIMIT 1''', tuple)

	if len(res) == 0:
		return False

	nzbpath = os.path.join(os.path.expanduser(nzbdir), str(res[0][0])[0], res[0][0] + '.nzb.gz')
	if os.path.isfile(nzbpath) == True:
		try:
			shutil.copy(nzbpath, os.path.join(os.path.expanduser(watchdir), '[rsigh] ' + dirname + '.nzb.gz'))
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			sys.exit(1)
		return True
	else:
		return False

def delete(sqlite, dirname, nzbdir, tchdir):
	tuple = (dirname,)
	res = sqlite.query('''SELECT volume FROM rsigh WHERE dirname = ? LIMIT 1''', tuple)

	if len(res) == 0:
		return False

	nzbpath = os.path.join(os.path.expanduser(nzbdir), str(res[0][0])[0], res[0][0] + '.nzb.gz')
	tchpath = os.path.join(os.path.expanduser(tchdir), str(res[0][0])[0], res[0][0] + '.tch')
	if os.path.isfile(nzbpath) == True and os.path.isfile(tchpath) == True:
		sqlite.execute('''DELETE FROM rsigh WHERE dirname = ?''', tuple)
		os.unlink(nzbpath)
		os.unlink(tchpath)
		return True
	else:
		return False

def gzcompress(filename, unlink=True):
	if os.path.isfile(filename):
		with open(filename, 'rb') as f_in:
			with gzip.open(filename + '.gz', 'wb') as f_out:
				try:
					f_out.writelines(f_in)
				except:
					if len(str(sys.exc_info()[1])) > 0:
						print(sys.exc_info()[1])
					return False

	if unlink == True:
		os.unlink(filename)

	return True

def postproc(sqlite, args, input):
	input = os.path.normpath(input) + os.sep
	tuple = (os.path.dirname(input)[8:],)
	res = sqlite.query('''SELECT * FROM rsigh WHERE dirname = ? LIMIT 1''', tuple)

	if len(res) == 0:
		return False

	if os.path.isfile(os.path.join(input, res[0][2] + '.par2')):
		par2 = PAR2(filename=os.path.join(input, res[0][2] + '.par2', binary=args['par2_bin']))
		if par2.verify() == False:
			if par2.repair() == False:
				sys.exit(1)

	if os.path.isfile(os.path.join(input, res[0][2] + '.rar')):
		if res[0][5] is not None:
			rar_password = str(res[0][5])
		else:
			rar_password = None
		rar = RAR(filename=os.path.join(input, res[0][2] + '.rar'), password=rar_password, binaries=(args['rar_bin'], args['unrar_bin']))
		if rar.unrar() == False:
			sys.exit(1)

	if os.path.isfile(os.path.join(input, res[0][2] + '.tc')):
		tc = TrueCrypt(filename=os.path.join(input, res[0][2] + '.tc'), binary=args['truecrypt_bin'])
		volume_headers = tc.read_tch(filename=os.path.join(os.path.expanduser(args['tch_dir']), str(res[0][2])[0], res[0][2] + '.tch'))
		if len(volume_headers) == 0:
			sys.exit(1)

		tc.restore_headers(volume_headers)

		passwords = (res[0][3], res[0][4])

		if len(volume_headers) == 2:
			tc.mount(passwords, hidden=True)
		elif len(volume_headers) == 1:
			tc.mount(passwords, hidden=False)
		else:
			sys.exit(1)

		if os.path.isdir(os.path.join(input, res[0][2], res[0][1])):
			try:
				shutil.move(os.path.join(input, res[0][2], res[0][1]), os.path.join(input, os.pardir) + os.sep + (input)[8:])
			except:
				if len(str(sys.exc_info()[1])) > 0:
					print(sys.exc_info()[1])
				sys.exit(1)
		elif os.path.isfile(os.path.join(input, res[0][2], res[0][1])):
			try:
				shutil.move(os.path.join(input, res[0][2], res[0][1]), os.path.join(input, os.pardir))
			except:
				if len(str(sys.exc_info()[1])) > 0:
					print(sys.exc_info()[1])
				sys.exit(1)			

		if tc.dismount(force=True, unlink=True) == False:
			sys.exit(1)

		try:
			shutil.rmtree(input)
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			sys.exit(1)

	return True

def main():
	config = init_configparser()
	args = init_argparse(config)

	input = args['input']

	sqlite = init_sqlite(args['sqlite_db'])

	if args['search'] == True and input != '.':
		search(sqlite, input)
		sys.exit()

	if args['collect'] == True and input != '.':
		if collect(sqlite, input, nzbdir=os.path.expanduser(args['nzb_dir']), watchdir=os.path.expanduser(args['watch_dir'])) == True:
			print('%s.nzb.gz > %r' % (input, os.path.expanduser(args['watch_dir'])))
		else:
			print('%r not found.' % input)

		sys.exit()

	if args['dupecheck'] == True and input != '.':
		if dupecheck(sqlite, input) == True:
			sys.exit(0)
		else:
			sys.exit(1)

	if args['list'] == True:
		list(sqlite, limit=50)
		sys.exit()

	if args['list_old'] == True:
		listold(sqlite, retention=args['retention'], limit=50)
		sys.exit()

	if args['delete'] == True:
		delete(sqlite, input, nzbdir=os.path.expanduser(args['nzb_dir']), tchdir=os.path.expanduser(args['tch_dir']))
		sys.exit()

	if args['post_process'] == True and input != '.':
		if postproc(sqlite, args, input) == True:
			sys.exit(0)
		else:
			sys.exit(1)

	if args['sqlite_vacuum'] == True:
		sqlite.execute('''VACUUM''')
		sys.exit()

	input = os.path.normpath(input)
	if input == '.' or not os.path.exists(input):
		sys.exit()

	if dupecheck(sqlite, input) == False:
		sys.exit(1)

	global temp
	temp = os.path.normpath(os.path.expanduser(args['tmp_dir'])) + os.sep + 'rsigh-tmp-' + str(os.getpid()) + os.sep

	filename = str(uuid.uuid4())
	while volcheck(sqlite, filename) == False:
		filename = str(uuid.uuid4())
	filename=temp + filename

	if not os.path.isdir(temp):
		try:
			os.makedirs(temp)
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			sys.exit(1)

	signal.signal(signal.SIGINT, handler)

	passwords = []
	tc = TrueCrypt(filename=filename + '.tc', binary=args['truecrypt_bin'])
	if tc == False:
		rmtmp()
		sys.exit(1)

	passwords.append(tc.create((((filesize(input)*1.10)+1310720)), password=args['tc_ov_password'], enc_algorithm=args['tc_encryption_algo'], \
		hash_algorithm=args['tc_hash_algo'], filesystem=args['tc_filesystem'], random_char_length=args['tc_randcharlen']))

	if args['tc_volume_type'] == 'hidden':
		passwords.append(tc.create((((filesize(input)*1.075)+655360)), password=args['tc_hv_password'], type='hidden', enc_algorithm=args['tc_encryption_algo'], \
			hash_algorithm=args['tc_hash_algo'], filesystem=args['tc_filesystem'], random_char_length=args['tc_randcharlen']))

	if args['tc_volume_type'] == 'hidden':
		tc.mount(passwords, hidden=True)
	else:
		tc.mount(passwords, hidden=False)

	if os.path.isfile(input):
		try:
			shutil.copy(input, os.path.join(temp, filename) + os.sep)
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			rmtmp()
			sys.exit(1)
	elif os.path.isdir(input):
		try:
			shutil.copytree(input, os.path.join(temp, filename, os.path.basename(input)) + os.sep)
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			rmtmp()
			sys.exit(1)

	if tc.dismount(force=True, unlink=True) == False:
		rmtmp()
		sys.exit(1)

	if tc.backup_headers(tofile=True, overwrite=True) == False:
		rmtmp()
		sys.exit(1)
	tchdir = os.path.expanduser(args['tch_dir'])
	if not os.path.isdir(os.path.join(tchdir, os.path.basename(filename)[0])):
		try:
			os.makedirs(os.path.join(tchdir, os.path.basename(filename)[0]))
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			rmtmp()
			sys.exit(1)
	try:
		shutil.move(filename + '.tch', os.path.join(tchdir, os.path.basename(filename)[0]))
	except:
		if len(str(sys.exc_info()[1])) > 0:
			print(sys.exc_info()[1])
		rmtmp()
		sys.exit(1)

	rar_password = tc.random_string(64)
	rar = RAR(filename=os.path.basename(filename) + '.rar', password=rar_password, binaries=(args['rar_bin'], args['unrar_bin']))	
	if rar == False:
		rmtmp()
		sys.exit(1)
	if rar.create(temp) == False:
		rmtmp()
		sys.exit(1)

	if tc.destroy_volume(unlink=True) == False:
		rmtmp()
		sys.exit(1)

	if args['no_par2'] == False:
		par2 = PAR2(filename=os.path.basename(filename) + '.par2', binary=args['par2_bin'])
		if par2 == False:
			rmtmp()
			sys.exit(1)
		if par2.create(temp, opts='-r%s -n%s' % (args['par2_redundancy'], args['par2_number'])) == False:
			rmtmp()
			sys.exit(1)

	if args['no_post'] == True:
		sys.exit(0)

	cwd = os.getcwd()
	os.chdir(temp)
	sp = subprocess.Popen('%s %s -c %s -g %s -f %s %s' % (args['python2_bin'], args['nm_script'], args['nm_config'], args['nm_group'], \
		os.path.basename(filename), ','.join(os.listdir(temp)).replace(',', ' ')), shell=True, stdin=subprocess.PIPE)
	sp.communicate()
	os.chdir(cwd)
	if sp.returncode > 0:
		rmtmp()
		sys.exit(1)
	else:
		tuple = (os.path.basename(input), os.path.basename(filename), passwords[0], passwords[1], rar_password, str(time.time()).split('.')[0])
		sqlite.execute('''INSERT INTO rsigh (dirname, volume, ov_password, hv_password, rar_password, posted) VALUES (?, ?, ?, ?, ?, ?)''', tuple)

		nzbdir = os.path.expanduser(args['nzb_dir'])
		if not os.path.isdir(os.path.join(nzbdir, os.path.basename(filename)[0])):
			try:
				os.makedirs(os.path.join(nzbdir, os.path.basename(filename)[0]))
			except:
				if len(str(sys.exc_info()[1])) > 0:
					print(sys.exc_info()[1])
				rmtmp()
				sys.exit(1)
		try:
			shutil.move(os.path.join(temp, 'newsmangler_' + os.path.basename(filename) + '.nzb'), \
				os.path.join(nzbdir, os.path.basename(filename)[0], os.path.basename(filename) + '.nzb'))
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			rmtmp()
			sys.exit(1)
		
		gzcompress(os.path.join(nzbdir, os.path.basename(filename)[0], os.path.basename(filename) + '.nzb'), unlink=True)

if __name__ == '__main__':
		main()
		rmtmp()
		sys.exit(0)