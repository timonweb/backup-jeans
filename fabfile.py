"""
BACKUP JEANS: Files / database backup script powered by Duplicity and Fabric.

Copyright (c) 2015 timonweb.com and contributors.
All rights reserved.

LICENSE:

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import uuid
import sys

from fabric.api import hide, task, settings, local, shell_env
from fabric.operations import prompt


"""
1. CONFIGURATION
...
"""

# Enter a unique name for this backup script to distinguish it, you can use a domain name, for example.
BACKUP_NAME = 'djtim.dev'


"""
1.1 BACKUP TARGET SETTINGS
"""


# Amazon S3 Information
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""

# Backup targets (In Duplicity format). You can backup to several destinations at once!
TARGETS = [
    's3+http://mybucketname',
]

# If you aren't running this from a cron, comment this line out and duplicity should prompt you for your password.
PASSPHRASE = ""


"""
1.2 FILES BACKUP SETTINGS
"""


# The SOURCE_DIR of your backup (where you want the backup to start). This can be / or somwhere else.
SOURCE_DIR = "/var/www/example.com"

# This is a list of directories to include.
#
# Example:
# INCLUDE = [ "/home/*/Documents", "/home/www/mysql-backups" ]
INCLUDE = []

# A list of directories, files, wildcard that you want to exclude from files backup.
#
# Example:
# EXCLUDE = ["/home/*/Projects/Completed", "/**.DS_Store", "/**Icon?"]
EXCLUDE = [
    '/**.git',
    '/**.git/*',
    '/**.DS_Store',
    '/**.idea*',
]

# Do a full files backup if older than 3days. You can change it to any number.
FILES_FULL_IF_OLDER_THAN = '3D'

# Remove files backups older than 14 days, you can change it to any number.
FILES_REMOVE_OLDER_THAN = '14D'


"""
1.3 DATABASE BACKUP SETTINGS
"""


# Database type: postgres or mysql.
DB_TYPE = 'postgres'

# Database credentials.
DB_NAME = ''
DB_USER = ''
DB_PASS = ''

# Do a full database backup if older than 3days. You can change it to any number.
DB_FULL_IF_OLDER_THAN = '3D'

# Remove database backups older than 14 days, you can change it to any number.
DB_REMOVE_OLDER_THAN = '14D'


"""
1.4 CRON SETTINGS
"""


# Cron schedule for database backups in cron format.
FILES_CRON_SCHEDULE = '10 12 * * *'

# Cron schedule for database backups in cron format.
DB_CRON_SCHEDULE = '5 12 * * *'

# Email address to send reports to on failed backups.
SEND_REPORTS_ADDRESS = 'admin@localhost'


"""
1.5 MISC SETTINGS
"""


# Storage subdir names
# Files and database will be saved in separate directories / buckets on your target, so you could easily distinguish
# what is what.
DB_SUBDIR = 'db'
FILES_SUBDIR = 'files'


"""
2. TASKS
...
"""

@task
def backup_files(options=''):
    """
    Backup files from SOURCE_DIR to TARGETS
    """
    if len(INCLUDE) > 0:
        options += ' '.join([' --include "{}"'.format(item) for item in INCLUDE])
    if len(EXCLUDE) > 0:
        options += ' '.join([' --exclude "{}"'.format(item) for item in EXCLUDE])

    file_backup(
        SOURCE_DIR,
        subdir=FILES_SUBDIR,
        options=options,
        full_if_older_than=FILES_FULL_IF_OLDER_THAN,
        remove_older_than=FILES_REMOVE_OLDER_THAN
    )


@task
def backup_db(options=''):
    """
    Backup database to TARGETS
    """
    tmp_dirname = '/tmp/duplicity-{}'.format(uuid.uuid4())
    tmp_filename = '{}/dump.sql'.format(tmp_dirname)
    local('mkdir -p {}'.format(tmp_dirname))

    if DB_TYPE == 'postgres':
        with shell_env(PGPASSWORD=DB_PASS):
            local('pg_dump -U {} {} -f {} -h 127.0.0.1'.format(DB_USER, DB_NAME, tmp_filename))
    elif DB_TYPE == 'mysql':
        local('mysqldump -u {} -p{} {} > {}'.format(DB_USER, DB_PASS, DB_NAME, tmp_filename))

    file_backup(
        tmp_dirname,
        subdir=DB_SUBDIR,
        options=options + ' --allow-source-mismatch',
        full_if_older_than=DB_FULL_IF_OLDER_THAN,
        remove_older_than=DB_REMOVE_OLDER_THAN
    )


@task
def restore_files(dest, target_id=0, subdir=FILES_SUBDIR, file_to_restore=None, time=None):
    """
    Restore files from a TARGET
    """
    options = []
    target = TARGETS[target_id]
    if subdir:
        target += '/' + subdir
    if file_to_restore:
        options.append('--file-to-restore {}'.format(file_to_restore))
    if time:
        options.append('--time {}'.format(time))
    duplicity_command('restore {} {} {}'.format(' '.join(options), target, dest))


@task
def restore_db(dest, target_id=0, time=None):
    """
    Restore database from a TARGET
    """
    restore_files(dest, target_id=target_id, subdir=DB_SUBDIR, time)


@task
def list_current_files(target_id=0, time=None):
    """
    List current files in TARGETS
    """
    target = TARGETS[target_id]
    options = []
    if time:
        options.append('--time {}'.format(time))
    duplicity_command('list-current-files {} {}'.format(' '.join(options), target))


@task
def duplicity_command(args=''):
    """
    Execute duplicity command with args and necessary parameters preinjected.
    """
    args += ' --s3-use-new-style --asynchronous-upload'
    if len(PASSPHRASE) == 0:
        args += ' --no-encryption'
    with shell_env(
            AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID,
            AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY,
            PASSPHRASE=PASSPHRASE
    ):
        local('duplicity {}'.format(args))


@task
def cron_setup(skip_confirmation=False, verify_cronjob=False):
    """
    Set up regular backup cronjob
    """
    cron_tasks = {}
    fabfile_dir = os.path.dirname(os.path.realpath(__file__))
    fab_path = fab_bin_path()

    # Gather cron tasks we wish to add
    if SEND_REPORTS_ADDRESS and len(SEND_REPORTS_ADDRESS) > 7:
        cron_tasks['mailto'] = 'MAILTO={}'.format(SEND_REPORTS_ADDRESS)

    if FILES_CRON_SCHEDULE and len(FILES_CRON_SCHEDULE) > 0:
        cron_tasks['backup_files'] = '{} cd {} && {} backup_files --hide output,running,warnings > /dev/null'.format(
            FILES_CRON_SCHEDULE,
            fabfile_dir,
            fab_path
        )

    if DB_CRON_SCHEDULE and len(DB_CRON_SCHEDULE) > 0:
        cron_tasks['backup_db'] = '{} cd {} && {} backup_db --hide output,running,warnings > /dev/null'.format(
            DB_CRON_SCHEDULE,
            fabfile_dir,
            fab_path
        )

    # Offer to test job before we add it.
    if not skip_confirmation:
        reply = prompt(
            "\nBefore creating a cronjob, would you like to verify if your backup is setup correctly?"
            "\nWell do a dry run and if errors arise, we won't create a cron job (yes/no)"
        )

        if reply.lower() == "yes":
            verify_cronjob = True

    # Do a dry run for enabled cron tasks
    if verify_cronjob:
        try:
            if cron_tasks.get('backup_files'):
                backup_files(options='--dry-run')
            if cron_tasks.get('backup_files'):
                backup_db(options='--dry-run')
        except (SystemExit, SystemError) as err:
            sys.stderr.write("\nError has occurred during backup check! Aborting!\n")
            return False

    # Ask user before creating a cronjob
    if not skip_confirmation:

        reply = prompt(
            "\n\nThese lines will be added to your crontab:"
            "\n%s"
            "\nWould you like to continue? (yes/no) "
            % '\n'.join([cron_tasks.get(key, '') for key in crontab_get_tasks()])
        )

        if reply.lower() != "yes":
            sys.stderr.write("\nAborting!\n")
            return False

    # Add / update tasks and remove not enabled.
    for task in crontab_get_tasks():
        marker = crontab_make_marker(task)
        if cron_tasks.get(task):
            crontab_update(cron_tasks[task], marker)
        else:
            crontab_remove(marker)

    sys.stdout.write('Done, your can see your crontab with "crontab -l" command')


@task
def cron_remove():
    """
    Remove all cronjobs related to this backup
    """
    for task in crontab_get_tasks():
        marker = crontab_make_marker(task)
        crontab_remove(marker)
    sys.stdout.write(
        'Done, we removed tasks for your backup project {}, use "crontab -l" command to check.'.format(BACKUP_NAME))


"""
3. UTILS
...
"""


"""
3.1 MISC
"""


def fab_bin_path():
    """
    Returns bin path of fabric executable or fails.
    """
    with settings(hide('warnings', 'stdout', 'running'), warn_only=True):
        output = local('which fab', capture=True)
        if output.succeeded:
            return output
        else:
            raise Exception("Fab executable wasn't found!")


def file_backup(source, subdir=None, options='', full_if_older_than='3D', remove_older_than='14D'):
    """
    Backs up files in source, removes old backups.
    """
    for target in TARGETS:
        if subdir:
            target += '/' + subdir
        duplicity_command('{} {} {} --full-if-older-than {}'.format(options, source, target, full_if_older_than))
        duplicity_command('remove-older-than {} {} --force'.format(remove_older_than, target))


"""
3.2 CRONTAB
"""


def crontab_get_tasks():
    """
    Holds cronjob task names
    """
    return ['mailto', 'backup_files', 'backup_db']


def crontab_make_marker(task):
    """
    Generic function to build a marker
    """
    return 'duplicity_{}_{}'.format(BACKUP_NAME, task)


def crontab_marker(marker):
    return ' # MARKER:%s' % marker if marker else ''


def crontab_get_current():
    """
    Get curren crontab
    """
    with settings(hide('warnings', 'stdout', 'running'), warn_only=True):
        output = local('crontab -l', capture=True)
        return output if output.succeeded else ''


def crontab_set(content):
    """
    Sets crontab content
    """
    with hide('output', 'running'), settings(warn_only=True):
        local("echo '%s' | crontab -" % content)


def crontab_add(content, marker=None):
    """
    Adds line to crontab. Line can be appended with special marker
    comment so it'll be possible to reliably remove or update it later.
    """
    old_crontab = crontab_get_current()
    crontab_set(old_crontab + '\n' + content + crontab_marker(marker))


def crontab_remove(marker):
    """
    Removes a line added and marked using crontab_add.
    """
    lines = [line for line in crontab_get_current().splitlines()
             if line and not line.endswith(crontab_marker(marker))]
    crontab_set("\n".join(lines))


def crontab_update(content, marker):
    """
    Adds or updates a line in crontab.
    """
    crontab_remove(marker)
    crontab_add(content, marker)