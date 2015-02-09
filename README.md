# backup-jeans

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

# Configuration #

Edit downloaded ***tasks.py***, find section 1 configuration and enter your data in lines marked as #CHANGEME. 

## 3. Usage ##

You can see all commands available by running `invoke --list` command. To get individual per command help, use `invoke --help <command_name>`, for example `invoke --help backup_files` to get a help for backup_files function.

Main functions of the script are: `invoke backup_files` and `invoke backup_db`, these do run backups of your files and database respectivelly. 

You can test if your backup configuration is correct by running `invoke backup_files_verify` or `invoke backup_db_verify`. ***Backup jeans*** will do a --dry-run and will output results on the screen.

Now you can setup a cronjob to execute these commands on a schedule.

## 4. Automatic cronjob setup ##
***Backup jeans*** can automatically setup a cronjob for you. To do so run `invoke cron_setup` and follow on screen instructions.

## 5. Restoring backups ##

To restore your project files run `invoke restore_files --dest=/path/where/to/restore` and ***backup jeans*** will restore your latest backup into /path/where/to/restore directory. If you want to restore a file from a given timeframe, you can use a time option. For example, let's restore files that we've backed up 3 days ago: `invoke restore_files --dest=/path/where/to/restore --time=3D`. For more available options, please refer to command help `invoke --help restore_files`

# NOTE: # 
While this script totally works for me, it may contain bugs, so be careful and check if your cronjobs are executed properly. Also as a good practice, don't forget to test your backups on a regular basis.
