Hi,

This is a full working minecraft server (well almost) just run the start script and it starts working.

# Deployment


# Usage
Start server:
- Would reccomend putting in tmux window
- run "./mc/start.sh"
- alternatively use systemctl

Rcon:
- "./mc/rcon.sh"

# Connecting
Forward port 25565 for players to connect to server and 25575 as well (for rcon to work correctly).
Look up your ip (google it) or use terminal
Mc server ip is host ip. Once correctly forwarded, anyone can connect



# Additional bonuses

## Auto backup
Regularly runs backup script which backs up server and deletes backups older than 14 days in backup folder

### Open crontab editor
crontab -e

0 3 */2 * * /Users/YOUR_USERNAME/minecraft-server/mc/backup.sh >> /Users/YOUR_USERNAME/minecraft-server/backups/backup.log 2>&1

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
