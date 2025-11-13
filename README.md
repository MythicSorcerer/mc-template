Hi,

This is a full working minecraft server (well almost) just run the start script and it starts working.

Cronjob

# Open crontab editor
crontab -e

0 3 */2 * * /Users/YOUR_USERNAME/minecraft-server/mc/backup.sh >> /Users/YOUR_USERNAME/minecraft-server/backups/backup.log 2>&1


# Every 48 hours at 3 AM
0 3 */2 * *

# Every day at 3 AM (24 hours)
0 3 * * *

# Every 6 hours
0 */6 * * *

# Twice a day (3 AM and 3 PM)
0 3,15 * * *
