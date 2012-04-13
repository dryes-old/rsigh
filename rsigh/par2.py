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

import os,subprocess,sys

##TODO: optimise create() opts.

class PAR2:
	def __init__(self, filename=None, binary=None):
		self.filename = filename
		if binary == None:
			if os.name == 'posix':
				self.binary = '/usr/bin/par2'
			elif os.name == 'nt':
				self.binary = 'par2'
		else:
			self.binary = binary

		if not os.path.isfile(self.binary):
			return False

	def create(self, path, opts=''):
		if os.path.isdir(path):
			path = os.path.normpath(path) + os.sep
			if self.filename is None:
				self.filename = os.path.join(os.path.dirname(path), os.path.dirname(path).split(os.sep)[-1] + '.par2')
			filelist = ','.join(os.listdir(path)).replace(',', ' ')
		elif os.path.isfile(path):
			if self.filename is None:
				self.filename = os.path.splitext(path)[0] + '.par2'
			filelist = '%r' % (os.path.basename(path))
		else:
			return False

		cwd = os.getcwd()
		os.chdir(os.path.dirname(path))
		sp = subprocess.Popen('%s c %s %r %s' % (self.binary, opts, self.filename, filelist), shell=True, stdin=subprocess.PIPE)
		sp.communicate()
		os.chdir(cwd)
		if sp.returncode == 0:
			return True
		else:
			return False


	def verify(self, opts=''):
		sp = subprocess.Popen('%s v %s -- %r' % (self.binary, opts, self.filename), shell=True, stdin=subprocess.PIPE)
		sp.communicate()
		if sp.returncode == 0:
			return True
		else:
			return False

	def repair(self, opts=''):
		sp = subprocess.Popen('%s r %s -- %r' % (self.binary, opts, self.filename), shell=True, stdin=subprocess.PIPE)
		sp.communicate()
		if sp.returncode == 0:
			return True
		else:
			return False
