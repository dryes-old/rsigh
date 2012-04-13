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

import os,re,subprocess,sys

##TODO: drastically improve caluclate_volsize();

class RAR:
	def __init__(self, filename=None, password=None, binaries=None):
		self.filename = filename
		self.password = password
		self.binary = []
		if binaries == None:
			if os.name == 'posix':
				self.binary.append('/usr/bin/rar')
				self.binary.append('/usr/bin/unrar')
			elif os.name == 'nt':
				self.binary.append('rar')
				self.binary.append('unrar')
		else:
			self.binary = binaries

		if not os.path.isfile(self.binary[0]) or not os.path.isfile(self.binary[1]):
			return False

	def create(self, path, compression='-m0', volsize=None, opts='-ep -ierr -vn -y'):
		if os.path.isdir(path):
			path = os.path.normpath(path) + os.sep
			if self.filename is None:
				self.filename = os.path.join(os.path.dirname(path), os.path.dirname(path).split(os.sep)[-1] + '.rar')
			filelist = ','.join(os.listdir(path)).replace(',', ' ')
		elif os.path.isfile(path):
			if self.filename is None:
				self.filename = os.path.splitext(path)[0] + '.rar'
			filelist = '%r' % (os.path.basename(path))
		else:
			return False

		if os.path.exists(self.filename):
			return False

		if volsize is not None:
			opts += ' -v%s' % volsize
		else:
			opts += ' -v%sb' % (self.calculate_volsize(path))

		if self.password is not None:
			opts += ' -hp%s' % re.escape(self.password)

		cwd = os.getcwd()
		os.chdir(os.path.dirname(path))
		sp = subprocess.Popen('%s a %r %s %s %s --' % (self.binary[0], self.filename, filelist, compression, opts), shell=True, stdin=subprocess.PIPE)
		sp.communicate()
		os.chdir(cwd)
		if sp.returncode == 0:
			return True
		else:
			return False

	def calculate_volsize(self, path):
		filesize = 0
		if os.path.isdir(path):
			for dirpath, dirnames, filenames in os.walk(path):
				for f in filenames:
					filesize += os.path.getsize(os.path.join(dirpath, f))
		elif os.path.isfile(path):
			filesize = os.path.getsize(path)

		return (filesize/25)

	def unrar(self, opts='-ierr -o+ -y'):
		if self.password is not None:
			opts += ' -p%s' % re.escape(self.password)
		sp = subprocess.Popen('%s x %r %r/ %s --' % (self.binary[1], self.filename, os.path.dirname(self.filename), opts), shell=True, stdin=subprocess.PIPE)
		sp.communicate()
		if sp.returncode == 0:
			return True
		else:
			return False
