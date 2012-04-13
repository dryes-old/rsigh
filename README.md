rsigh
=====

rsigh is a Python script (*nix only) for posting passworded and encrypted files to Usenet.

* TrueCrypt volumes with headers stripped ensure your files are virtually inaccessible.
* Ability to search and retrieve NZBs from command line - no manual work reqd.
* Post-process function for easy restoration.

## dependencies:

* [Python3][python]
* [TrueCrypt][truecrypt]
* [par2cmdline][par2cmdline]
* [RAR][rar]
* [UnRAR][unrar]
* [newsmangler][newsmangler]


## usage:

* Simply download, retaining directory structure (including docs/), and run rsigh.py (-h for help).
* Config is copied to ~/.config/rsigh/rsigh.cfg if not found.
* Default storage directory is ~/.rsigh/ - including nzbs, tchs and SQLite databases.


## notes:

* newsmangler config should be setup before running.
* To run without constant requests for root password see: [archwiki]
* OSX users require: sudo ln -s /Applications/TrueCrypt.app/Contents/MacOS/TrueCrypt /usr/local/bin/truecrypt

* Do not attempt to enter 320 random characters when it asks - this is automated.

* Although your files are encrypted and passworded, Usenet is a public forum.
* Do not upload any files you consider to be sensitive or may land you in legal trouble (should they be accessed).

[python]: http://www.python.org/
[truecrypt]: http://www.truecrypt.org/
[par2cmdline]: https://github.com/BlackIkeEagle/par2cmdline
[rar]: http://www.rarlab.com/
[unrar]: http://www.rarlab.com/
[newsmangler]: https://github.com/madcowfred/newsmangler
[archwiki]: https://wiki.archlinux.org/index.php/TrueCrypt#Method_1_.28Add_a_truecrypt_group.29