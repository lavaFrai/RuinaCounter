docker stop ruina_counter
docker rm ruina_counter
docker run -it -d -v $(pwd):/opt/app --restart=always -p 8081:80 --name=ruina_counter $(docker build -q .)