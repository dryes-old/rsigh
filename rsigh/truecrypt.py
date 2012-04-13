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

import os,random,re,string,subprocess,sys

##TODO: NT support?
#https://wiki.archlinux.org/index.php/TrueCrypt#Method_1_.28Add_a_truecrypt_group.29
#OSX: ln -s /Applications/TrueCrypt.app/Contents/MacOS/TrueCrypt /usr/local/bin/truecrypt

class TrueCrypt:
	def __init__(self, filename, binary=None):
		self.filename = filename
		self.mountpath = None
		if binary == None:
			if os.name == 'posix':
				self.binary = '/usr/bin/truecrypt'
			elif os.name == 'nt':
				self.binary = 'truecrypt'
		else:
			self.binary = binary

		if not os.path.isfile(self.binary):
			return False

		if os.name == 'posix':
			self.nix_modprobe()

	def random_string(self, length=64):
		return ''.join([random.choice(string.digits + string.ascii_letters + string.punctuation + ' ') for _ in range(length)])

	def create(self, filesize, password=None, type='normal', enc_algorithm='AES', hash_algorithm='RIPEMD-160', filesystem='FAT', keyfiles=None, random_char_length=320):
		if password == None:
			password = self.random_string(64)
		opts = '-t -c --volume-type=%s --size=%s --encryption=%s --hash=%s --filesystem=%s %r' % (type, filesize, enc_algorithm, hash_algorithm, filesystem, self.filename)

		if keyfiles == None:
			opts += ' --keyfiles=\'\''
		else:
			opts += ' --keyfiles=%s' % (keyfiles)

		sp = subprocess.Popen('%s %s --password=%s' % (self.binary, opts, re.escape(password)), shell=True, stdin=subprocess.PIPE)
		sp.communicate(input=str.encode(self.random_string(random_char_length)))
		if sp.returncode > 0:
			return False

		return password

	def create_keyfile(self, filename):
		sp = subprocess.Popen('%s --create-keyfile %r' % (self.binary, filename), shell=True, stdin=subprocess.PIPE)
		sp.communicate(input=str.encode(self.random_string(random_char_length)))
		if sp.returncode > 0:
			return False

		return filename

	def backup_headers(self, tofile=True, overwrite=False):
		oo = os.open(self.filename, os.O_RDWR)
		volume_headers = []
		volume_headers.append(os.read(oo, 131072))
		if overwrite == True:
			os.lseek(oo, 0, os.SEEK_SET)
			os.write(oo, os.urandom(131072))
		os.lseek(oo, -131072, os.SEEK_END)
		volume_headers.append(os.read(oo, 131072))
		if overwrite == True:
			os.lseek(oo, -131072, os.SEEK_END)
			os.write(oo, os.urandom(131072))
		os.close(oo)

		filename = os.path.splitext(self.filename)[0] + '.tch'

		if tofile == True:
			if not os.path.isfile(filename):
				try:
					oo = os.open(filename, os.O_CREAT)
				except:
					if len(str(sys.exc_info()[1])) > 0:
						print(sys.exc_info()[1])
					return False
				os.close(oo)
			oo = os.open(filename, os.O_WRONLY)
			os.write(oo, volume_headers[0] + volume_headers[1])
			os.close(oo)

		return (volume_headers[0], volume_headers[1])

	def read_tch(self, filename=None):
		if filename == None:
			filename = os.path.splitext(self.filename)[0] + '.tch'

		if not os.path.isfile(filename):
			return False

		oo = os.open(filename, os.O_RDONLY)
		volume_headers = []
		volume_headers.append(os.read(oo, 131072))
		os.lseek(oo, -131072, os.SEEK_END)
		volume_headers.append(os.read(oo, 131072))
		os.close(oo)

		return (volume_headers[0], volume_headers[1])

	def restore_headers(self, volume_headers):
		oo = os.open(self.filename, os.O_WRONLY)
		os.write(oo, volume_headers[0])
		os.lseek(oo, -131072, os.SEEK_END)
		os.write(oo, volume_headers[1])
		os.close(oo)

	def destroy_volume(self, unlink=True):
		oo = os.open(self.filename, os.O_WRONLY)
		os.write(oo, os.urandom(131072))
		os.lseek(oo, -131072, os.SEEK_END)
		os.write(oo, os.urandom(131072))
		os.close(oo)

		if unlink == True:
			try:
				os.unlink(self.filename)
			except:
				if len(str(sys.exc_info()[1])) > 0:
					print(sys.exc_info()[1])
				return False

		return True

	def mount(self, passwords, mountpath=None, hidden=False, ov_keyfiles=None, hv_keyfiles=None, opts='-t'):
		if hidden == True:
			if passwords[1] == None:
				return False
			password = passwords[1]
			opts += ' --protect-hidden=no'
			if hv_keyfiles == None:
				opts += ' --keyfiles=\'\''
			else:
				opts += ' --keyfiles=%s' % (hv_keyfiles)
		else:
			password = passwords[0]
			if ov_keyfiles == None:
				opts += ' --keyfiles=\'\''
			else:
				opts += ' --keyfiles=%s' % (ov_keyfiles)
			if passwords[1] == None:
				opts += ' --protect-hidden=no'
			else:
				opts += ' --protect-hidden=yes --protection-password=' + re.escape(passwords[1])
				if hv_keyfiles == None:
					opts += ' --protection-keyfiles=\'\''
				else:
					opts += ' --protection-keyfiles=%s' % (hv_keyfiles)

		if mountpath == None:
			self.mountpath = os.path.splitext(self.filename)[0] + os.sep
		else:
			self.mountpath = mountpath

		if not os.path.exists(self.mountpath):
			try:
				os.makedirs(self.mountpath)
			except:
				if len(str(sys.exc_info()[1])) > 0:
					print(sys.exc_info()[1])
				return False

		sp = subprocess.Popen('%s %s --password=%s %r %r' % (self.binary, opts, re.escape(password), self.filename, self.mountpath), shell=True)
		sp.communicate()
		if sp.returncode == 0:
			return True
		else:
			return False

	def dismount(self, force=False, unlink=False):
		if force == True:
			opts = '-d -f'
		else:
			opts = '-d'
		sp = subprocess.Popen('%s %s %r' % (self.binary, opts, self.filename), shell=True)
		sp.communicate()
		if sp.returncode > 0:
			return False

		if unlink == True and os.path.isdir(self.mountpath):
			try:
				os.removedirs(self.mountpath)
			except:
				import shutil
				try:
					shutil.rmtree(self.mountpath)
				except:
					if len(str(sys.exc_info()[1])) > 0:
						print(sys.exc_info()[1])
					return False

		return True

	def nix_modprobe(self, mods=['dm_crypt', 'loop']):
		sg = subprocess.getoutput('/usr/bin/lsmod | /usr/bin/cut -d\' \' -f1').split()
		del sg[0]
		for mod in mods:
			if not mod in sg:
				print('modprobe %s' % (mod))
				sp = subprocess.Popen('/usr/bin/sudo /sbin/modprobe %s' % (mod), shell=True)
				sp.communicate()
				if sp.returncode == 0:
					return True
				else:
					return False