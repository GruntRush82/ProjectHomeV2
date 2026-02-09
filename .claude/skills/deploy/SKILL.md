---
name: deploy
description: Deploy the latest code to the Digital Ocean droplet
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Deploy to Production

Deploy the Family Hub app to the Digital Ocean droplet. Follow these steps exactly:

1. **Commit and push** (if there are uncommitted changes, ask the user first):
   ```bash
   cd /home/felke/project-home && git push origin master
   ```

2. **Pull on the droplet**:
   ```bash
   ssh root@68.183.192.133 "cd /projecthome/ProjectHomeV2 && git pull"
   ```

3. **Rebuild and restart the Docker container** (DB is volume-mounted and persists across rebuilds):
   ```bash
   ssh root@68.183.192.133 "docker stop projecthome && docker rm projecthome && docker build -t projecthome /projecthome/ProjectHomeV2 && docker run -d --name projecthome -p 5000:5000 -v /projecthome/data:/app/instance --env-file /projecthome/ProjectHomeV2/.env --restart unless-stopped projecthome"
   ```

4. **Verify** the container is running:
   ```bash
   ssh root@68.183.192.133 "docker ps && docker logs projecthome --tail 10"
   ```

5. Report the result to the user.

If $ARGUMENTS contains "no-rebuild", skip step 3 and only pull the code (useful for config-only changes).

If $ARGUMENTS contains "reset-db", delete the persistent DB before starting the new container so the app creates a fresh one with the current schema:
   ```bash
   ssh root@68.183.192.133 "rm /projecthome/data/chores.db"
   ```
   Run this AFTER step 2 (git pull) and BEFORE step 3 (docker run). Warn the user that all data will be lost.
