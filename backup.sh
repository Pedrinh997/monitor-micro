#!/bin/bash
sudo docker exec -i monitor_micro-db-1 pg_dump -U postgres postgres > /mnt/d/backups/backup_$(date +%Y%m%d_%H%M%S).sql
echo "Backup criado em /mnt/d/backups/backup_$(date +%Y%m%d_%H%M%S).sql"
