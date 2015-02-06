# backup-jeans (docs in the works)

Backup Jeans is a backup script that has one goal: to make process of backing up site's database and files simple and hassleless no matter what stack / language / cms your web app is running on.

The script itself is a [PyInvoke](http://www.pyinvoke.org) script that uses [Duplicity](http://duplicity.nongnu.org/) to do scheduled backups.

# Installation #

## 1. Dependencies ##

***Backup jeans*** needs [PyInvoke](http://www.pyinvoke.org), [Duplicity](http://duplicity.nongnu.org/) and [Boto](http://docs.pythonboto.org/) to be installed on your system.

### 1.1 Approach 1 ###
If you're on a relatively fresh Debian installation, you can do:
`sudo apt-get install python-invoke duplicity python-boto`

### 1.2 Approach 2 (Recommended) ###

To make sure you have latest versions of dependencies it's better to install them trough Python's package manager called PIP:

### 1.2.1 Installing PIP (if you don't have it installed) ###

`sudo apt-get install python-pip`

### 1.2.2 Installing dependencies via PIP ###

`pip install invoke duplicity boto`, depending on your system, you may need to run this command as `sudo pip install invoke duplicity boto`.

## 2. Install script itself ##

You can put tasks.py anywhere you wish, but I reccommend to create a ***backup*** directory in your project and put it here, so it will leave there. You can git clone to this directory or just ``wget https://raw.githubusercontent.com/timonweb/backup-jeans/master/tasks.py``` and you're almost ready to go.

## 3. Configuration ##

### 3.1 Enter necessary data ###
Edit downloaded ***tasks.py*** and enter your database credentials, backup paths, targets, cron schedule and other settings in section 1. configuration.

### 3.2 Setup cronjob ###
***Backup jeans*** will automatically setup a cronjob for you, but before it will offer you to test if your backup configuration is correct. 

To do so, staying in a directory where your invoke.py lives run `invoke cron_setup` and follow on screen steps.

## 4. Enjoy ##
That's all, now you have your credentials in, cronjob set and you may forget about it (well, not entirelly, remember about the need of regular backup test, but this is another story and not the job for this script).

# Doing manual backups #

If you want to do backups manually, ***Backup jeans*** will help you too. Try to run `invoke --list` to see a list of commands available.

Running `invoke backup_files` will backup files to your destination, you can pass additional duplicity options to that command via duopts parameter as in this example: `invoke backup_files --duopts="--dry-run"`. For a list of duplicity options please refer official [duplicity documentation](http://duplicity.nongnu.org/duplicity.1.html).

You can also run `invoke backup_db` to backup your database. Currently, ***backup jeans*** supports postgres and mysql backups.

# Restoring backups #
## Restoring files ##
To restore your project files run `invoke restore_files --dest=/path/where/to/restore` and ***backup jeans*** will restore your latest backup into /path/where/to/restore directory.
