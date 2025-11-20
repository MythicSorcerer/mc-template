Hi,

This is a full working minecraft server (well almost) just run the start script and it starts working.

# Deployment
Open directory where you want minecraft folder to be.

Run the below command.
This command create a mc-template folder within the folder you are in and put all needed files within.
I would recommend deleting the .git folder for cleanliness and renaming the folder minecraft.

Run: 
```
git clone https://github.com/MythicSorcerer/mc-template.git
```


# Usage
Start server:
- Would reccomend putting in tmux window
- run below command from minecraft folder
- alternatively use systemctl
```
./mc/start.sh
```

Rcon:
- "./mc/rcon.sh"

Logs: 
- "./mc/log.sh"

Oldlogs:
- "./server/logs/unzipper" to unzip
```
cd logs/readable/
./catall | less
```

# Connecting
Forward port 25565 for players to connect to server and 25575 as well (for rcon to work correctly).
Look up your ip (google it) or use terminal
Mc server ip is host ip. Once correctly forwarded, anyone can connect

# Features
- Fabric server 1.21.10
- Client side vanilla experience
- Server side management and optimization mods

# Additional bonuses

## Auto backup
Regularly runs backup script which backs up server and deletes backups older than 14 days in backup folder

### Open crontab editor
crontab -e

0 3 */2 * * /path/to/mc/backup.sh >> /path/to/backups/backup.log 2>&1

## Every 48 hours at 3 AM
0 3 */2 * *

## Every day at 3 AM (24 hours)
0 3 * * *

## Every 6 hours
0 */6 * * *

## Twice a day (3 AM and 3 PM)
0 3,15 * * *

# Re-initialize rcon
- "./mc/init.sh"


# NOTICE
I do not own any of Mojang's code or Tiiffi's code used in this repository.
