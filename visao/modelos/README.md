# Modelos

`best.pt`: YOLO11n treinado no D-Fire por 30 épocas no Colab (GPU T4), 5,5 MB. É o peso usado pela API (`src/api.py`) e pelo vídeo em tempo real (`src/detectar_video.py`).

Ele é o único `.pt` que vai para o GitHub (exceção no `.gitignore`). Para treinar de novo, rode o notebook `notebooks/treino_avaliacao_yolo.ipynb`: o novo peso sai em `MyDrive/FogoCerto_visao/modelos/best.pt` e substitui este.
