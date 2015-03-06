"""
BACKUP JEANS: Files / database backup script powered by Duplicity and PyInvoke.

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

from invoke import run, task
from invoke.cli import parse
from invoke.exceptions import Exit, Failure
from invoke.loader import FilesystemLoader


"""
1. CONFIGURATION
...
"""

# Enter a unique name for this backup script to distinguish it, you can use a domain name, for example.
BACKUP_NAME = ''  # CHANGE ME!

"""
1.1 BACKUP TARGET SETTINGS
"""


# Amazon S3 Information
AWS_ACCESS_KEY_ID = ""  # CHANGE ME!
AWS_SECRET_ACCESS_KEY = ""  # CHANGE ME!

# Backup targets (in duplicity format). You can backup to several destinations at once!
TARGETS = [
    's3+http://mybucketname',  # CHANGE ME!
]

# If you aren't running this from a cron, comment this line out and duplicity should prompt you for your password.
PASSPHRASE = ""  # CHANGE ME!

"""
1.2 FILES BACKUP SETTINGS
"""


# The SOURCE_DIR of your backup (where you want the backup to start). This can be / or somewhere else.
SOURCE_DIR = "/var/www/example.com"  # CHANGE ME!

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
DB_NAME = ''  # CHANGE ME!
DB_USER = ''  # CHANGE ME!
DB_PASS = ''  # CHANGE ME!

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
SEND_REPORTS_ADDRESS = 'admin@localhost'  # CHANGE ME!

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


@task(help={
    'duopts': 'Additional duplicity options you may pass to "duplicity" backup command. For example --duopts="--dry-run"'
              'Refer duplicity man page for more options.',
    'show-errors-only': 'Hide command output except errors, useful for cron jobs to limit cram mails.'
})
def backup_files(duopts='', show_errors_only=False):
    """
    Backup files from SOURCE_DIR to TARGETS.
    Executes "duplicity" backup command with target, source, --include and --exclude options prefilled.
    """
    if len(INCLUDE) > 0:
        duopts += ' '.join([' --include "{}"'.format(item) for item in INCLUDE])
    if len(EXCLUDE) > 0:
        duopts += ' '.join([' --exclude "{}"'.format(item) for item in EXCLUDE])

    file_backup(
        SOURCE_DIR,
        subdir=FILES_SUBDIR,
        duopts=duopts,
        full_if_older_than=FILES_FULL_IF_OLDER_THAN,
        remove_older_than=FILES_REMOVE_OLDER_THAN,
        show_errors_only=show_errors_only
    )


@task(help={
    'duopts': 'Additional duplicity options you may pass to "duplicity" backup command. For example --duopts="--dry-run"'
              'Refer duplicity man page for more options.',
    'show-errors-only': 'Hide command output except errors, useful for cron jobs to limit cram mails.'
})
def backup_db(duopts='', show_errors_only=False):
    """
    Backup database from SOURCE_DIR to TARGETS.
    Makes a database dump and then backs it up with duplicity.
    Executes "duplicity" backup command with target, source, --include and --exclude options prefilled.
    """
    tmp_dirname = '/tmp/duplicity-{}'.format(uuid.uuid4())
    tmp_filename = '{}/dump.sql'.format(tmp_dirname)
    run('mkdir -p {}'.format(tmp_dirname))

    if DB_TYPE == 'postgres':
        os.environ["PGPASSWORD"] = DB_PASS
        run('pg_dump -U {} {} -f {} -h 127.0.0.1'.format(DB_USER, DB_NAME, tmp_filename))

    elif DB_TYPE == 'mysql':
        run('mysqldump -u {} -p{} {} > {}'.format(DB_USER, DB_PASS, DB_NAME, tmp_filename))

    file_backup(
        tmp_dirname,
        subdir=DB_SUBDIR,
        duopts=duopts + ' --allow-source-mismatch',
        full_if_older_than=DB_FULL_IF_OLDER_THAN,
        remove_older_than=DB_REMOVE_OLDER_THAN,
        show_errors_only=show_errors_only
    )


@task(help={
    'show-errors-only': 'Hide command output except errors.'
})
def backup_files_verify(show_errors_only=False):
    """
    Does a dry run of your files backup by calculating what would be done, but do not perform any backend actions.
    Useful to check if you've entered all credentials correctly.
    """
    backup_files(duopts='--dry-run', show_errors_only=show_errors_only)


@task(help={
    'show-errors-only': 'Hide command output except errors.'
})
def backup_db_verify(show_errors_only=False):
    """
    Does a test database dump and dry run of your database files backup by calculating what would be done,
    but do not perform any backend actions.
    Useful to check if you've entered all credentials correctly.
    """
    backup_db(duopts='--dry-run', show_errors_only=show_errors_only)


@task(help={
    'dest': 'Directory where you want to restore to.',
    'file-to-restore': 'This option may be given, causing only path to be restored instead of the entire contents '
                       'of the backup archive. path should be given relative to the root of the directory backed up.',
    'time': 'Specify the time from which to restore files. Refer duplicity\'s Time formats section'
            ' to see time formats available: http://duplicity.nongnu.org/duplicity.1.html#sect9',
    'duopts': 'Additional duplicity options you may pass to "duplicity restore: command.'
              ' For example --duopts="--dry-run" Refer duplicity man page for more options.',
    'target_id': 'Index of a target you want to restore from, if you have multiple, by default is set to 0',
})
def restore_files(dest, file_to_restore=None, time=None, duopts='', target_id=0, _subdir=FILES_SUBDIR):
    """
    Restore files from a TARGET by executing 'duplicity restore' command.
    """
    target = TARGETS[target_id]

    if _subdir:
        target += '/' + _subdir

    if file_to_restore:
        duopts += ' --file-to-restore {}'.format(file_to_restore)

    if time:
        duopts += ' --time {}'.format(time)

    duplicity_command('restore {} {} {}'.format(duopts, target, dest))


@task(help={
    'dest': 'Directory where you want to restore to.',
    'time': 'Specify the time from which to restore files. Refer duplicity\'s Time formats section'
            ' to see time formats available: http://duplicity.nongnu.org/duplicity.1.html#sect9',
    'duopts': 'Additional duplicity options you may pass to "duplicity restore" command. '
              ' For example --duopts="--dry-run" Refer duplicity man page for more options.',
    'target_id': 'Index of a target you want to restore from, if you have multiple, by default is set to 0',
})
def restore_db_file(dest, time=None, duopts='', target_id=0):
    """
    Restore database dump file from a TARGET by executing 'duplicity restore' command.
    """
    if time:
        duopts += ' --time {}'.format(time)

    restore_files(dest, target_id=target_id, _subdir=DB_SUBDIR, duopts=duopts)


@task(help={
    'time': 'Specify the time from which to restore files. Refer duplicity\'s Time formats section'
            ' to see time formats available: http://duplicity.nongnu.org/duplicity.1.html#sect9',
    'duopts': 'Additional duplicity options you may pass to "duplicity list-current-files" command. '
              ' For example --duopts="--dry-run" Refer duplicity man page for more options.',
    'target_id': 'Index of a target you want to restore from, if you have multiple, by default is set to 0',
})
def list_current_files(time=None, duopts='', target_id=0):
    """
    List current files in TARGET.
    """
    if time:
        duopts += ' --time {}'.format(time)

    target = TARGETS[target_id]
    duplicity_command('list-current-files {} {}'.format(duopts, target))


@task(help={
    'args': 'Arguments',
    'duopts': 'Additional duplicity options you may pass to duplicity command. For example --duopts="--dry-run"'
              'Refer duplicity man page for more options.',
    'show-errors-only': 'Hide command output except errors, useful for cron jobs to limit cram mails.'
})
def duplicity_command(args='', duopts='', show_errors_only=False):
    """
    Execute duplicity command with args and necessary parameters preinjected. It will execute the following command:
    duplicity [duopts] [args] --s3-use-new-style --asynchronous-upload
    """
    duopts += ' --s3-use-new-style --asynchronous-upload'
    if len(PASSPHRASE) == 0:
        duopts += ' --no-encryption'

    os.environ["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY_ID
    os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_ACCESS_KEY
    os.environ["PASSPHRASE"] = PASSPHRASE
    hide_mode = None
    if show_errors_only:
        hide_mode = 'out'
    run('duplicity {} {}'.format(duopts, args), hide=hide_mode)


@task(help={
    'skip-confirmation': 'Doesn\'t show confirmation step before creating a cron job.',
    'verify-cronjob': 'Set to True if you want to verify backup command before creating a cron job.',
    'show-errors-only': 'Hide command output except errors.'
})
def cron_setup(skip_confirmation=False, verify_cronjob=False, show_errors_only=False):
    """
    Set up regular backup cronjob in your system for the current user.
    """
    cron_tasks = {}
    fabfile_dir = os.path.dirname(os.path.realpath(__file__))
    invoke_path = invoke_bin_path()

    # Gather cron tasks we wish to add
    if SEND_REPORTS_ADDRESS and len(SEND_REPORTS_ADDRESS) > 7:
        cron_tasks['mailto'] = 'MAILTO={}'.format(SEND_REPORTS_ADDRESS)

    if FILES_CRON_SCHEDULE and len(FILES_CRON_SCHEDULE) > 0:
        cron_tasks['backup_files'] = '{} cd {} && {} backup_files --show-errors-only > /dev/null'.format(
            FILES_CRON_SCHEDULE,
            fabfile_dir,
            invoke_path
        )

    if DB_CRON_SCHEDULE and len(DB_CRON_SCHEDULE) > 0:
        cron_tasks['backup_db'] = '{} cd {} && {} backup_db --show-errors-only > /dev/null'.format(
            DB_CRON_SCHEDULE,
            fabfile_dir,
            invoke_path
        )

    # Offer to test job before we add it.
    if not skip_confirmation:
        reply = raw_input(
            "\nBefore creating a cronjob, would you like to verify if your backup is setup correctly?"
            "\nWell do a dry run and if errors arise, we won't create a cron job (yes/no): "
        )

        if reply.lower() == "yes":
            verify_cronjob = True

    # Do a dry run for enabled cron tasks
    if verify_cronjob:
        try:
            if cron_tasks.get('backup_files'):
                backup_files_verify(show_errors_only=show_errors_only)
            if cron_tasks.get('backup_files'):
                backup_db_verify(show_errors_only=show_errors_only)
        except (SystemExit, SystemError) as err:
            sys.stderr.write("\nError has occurred during backup check! Aborting!\n")
            return False

    # Ask user before creating a cronjob
    if not skip_confirmation:

        reply = raw_input(
            "\n\nThese lines will be added to your crontab:"
            "\n%s"
            "\nWould you like to continue? (yes/no): "
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

    sys.stdout.write('Done, your can see your crontab with "crontab -l" command \n')


@task
def cron_remove():
    """
    Remove all cronjobs related to this backup
    """
    for task in crontab_get_tasks():
        marker = crontab_make_marker(task)
        crontab_remove(marker)
    sys.stdout.write(
        'Done, we removed tasks for your backup project {}, use "crontab -l" command to check. \n'.format(BACKUP_NAME))


@task
def print_all_help():
    """
    Print help for all commands.
    """
    loader = FilesystemLoader()
    collection = loader.load()

    task_names = collection.task_names.keys()
    task_names.sort()
    for task_name in task_names:
        sys.stdout.write('\n{}:\n'.format(task_name))
        try:
            parse([invoke_bin_path(), '--help', task_name], collection)
        except Exit:
            pass

"""
3. UTILS
...
"""

"""
3.1 MISC
"""


def invoke_bin_path():
    """
    Returns bin path of fabric executable or fails.
    """
    output = run('which invoke', hide=True)
    if output.stdout:
        return output.stdout.strip('\n')
    else:
        raise Exception("Invoke executable wasn't found!")


def file_backup(source, subdir=None, duopts='', full_if_older_than='3D', remove_older_than='14D',
                show_errors_only=False):
    """
    Backs up files in source, removes old backups.
    """
    for target in TARGETS:
        if subdir:
            target += '/' + subdir
        duplicity_command('{} {} {} --full-if-older-than {}'.format(duopts, source, target, full_if_older_than),
                          show_errors_only=show_errors_only)
        duplicity_command('remove-older-than {} {} --force'.format(remove_older_than, target),
                          show_errors_only=show_errors_only)


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
    Get current crontab
    """
    try:
        output = run('crontab -l', hide=True)
        return output.stdout.strip('\n') if output.stdout else ''
    except Failure:
        # 'crontab -l' command issues Failure exception if user has no
        # cron jobs defined, we return empty string in such case
        return ''


def crontab_set(content):
    """
    Sets crontab content
    """
    run("echo '{}' | crontab -".format(content))


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
    if len(crontab_get_current()) > 0:
        lines = [line for line in crontab_get_current().splitlines()
                 if line and not line.endswith(crontab_marker(marker))]
        crontab_set("\n".join(lines))


def crontab_update(content, marker):
    """
    Adds or updates a line in crontab.
    """
    crontab_remove(marker)
    crontab_add(content, marker)