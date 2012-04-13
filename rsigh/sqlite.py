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

import sqlite3

class SQLite:
	def __init__(self, filename):
		try:
			self.sc = sqlite3.connect(filename)
		except:
			if len(str(sys.exc_info()[1])) > 0:
				print(sys.exc_info()[1])
			return False

	def execute(self, sql, tuple=None):
		cc = self.sc.cursor()

		if tuple == None:
			cc.execute(sql)
		else:
			cc.execute(sql, tuple)

		self.sc.commit()
		cc.close()
	
		return

	def query(self, sql, tuple=None):
		cc = self.sc.cursor()

		res = []
		if tuple == None:
			cc.execute(sql)
		else:
			cc.execute(sql, tuple)

		for row in cc:
			res.append(row)

		self.sc.commit()
		cc.close()
	
		return res