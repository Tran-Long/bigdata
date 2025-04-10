docker compose down
docker system prune -f
#!/bin/bash
volumes=$(docker volume ls | grep bigdata | awk '{print $2}')
if [ -z "$volumes" ]; then
    echo "No volumes found. Successful."
else
    docker volume rm $volumes && echo "Volumes removed successfully."
fi
