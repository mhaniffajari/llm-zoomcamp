# LLM Zoomcamp

## setup ollama

```
curl -fsSL https://ollama.com/install.sh | sh

ollama start
ollama pull phi3
```

## to test your LLM
you can use this
```
ollama run phi3
```
don't forget to type /bye after you test your LLM

## export your OPEN_AI_API_KEY


```
export OPEN_AI_API_KEY="openapi"
```

```
export MISTRAL_AI_API_KEY="mistralapi"
```


## setup elasticsearch with optimize performance
you must compromize your elasticsearch
```
docker run -it \
    --rm \
    --name elasticsearch \
    -p 9200:9200 \
    -p 9300:9300 \
    -e "discovery.type=single-node" \
    -e "xpack.security.enabled=false" \
    -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
    -e "xpack.ml.enabled=false" \
    docker.elastic.co/elasticsearch/elasticsearch:8.4.3
```

## setup elasticsearch
```
docker run -it \
    --rm \
    --name elasticsearch \
    -p 9200:9200 \
    -p 9300:9300 \
    -e "discovery.type=single-node" \
    -e "xpack.security.enabled=false" \
    elasticsearch:8.4.3
```

