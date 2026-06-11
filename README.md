# Лаба 7. Развертыване веб-сервиса в Kubernetes (Minikube) с мониторингом и автоскейлингом

Задачи:

1) развернуть minicube 

2) создать docker образ вашего приложения;

3) создать deployment;

4) установить кол-во подов на 3

5) добавьте Metrics Server (kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml).

6) настройте Horizontal Pod Autoscaler (HPA), чтобы масштабировать поды при увеличении нагрузки (kubectl autoscale deployment my-app --cpu-percent=50 --min=2 --max=5).

7) настройте Prometheus и Grafana через (helm install prometheus prometheus-community/kube-prometheus-stack). Настройте дашборды в Grafana для мониторинга нагрузки (хотя бы один)

# Инструкция

> *работа выполнялась в окружении WSL2*

---

## Шаг 1: Подготовка окружения и установка инструментов

Открываем терминал Ubuntu. Необходимо установить Docker, Minikube, утилиту управления `kubectl` и менеджер пакетов Helm.

### 1.1. Установка Docker

```bash
sudo apt update
sudo apt install -y docker.io
```

### 1.2. Установка kubectl (пульт управления кластером)

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### 1.3. Установка Minikube

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

### 1.4. Установка Helm (необходим для Grafana)

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Cкриншоты
<img width="1193" height="346" alt="image" src="https://github.com/user-attachments/assets/68969a6e-82de-49dd-8566-0057ea7ed91f" />


---

## Шаг 2: Запуск Minikube и привязка Docker-окружения

Запускаем локальный инстанс Kubernetes:

```bash
minikube start --driver=docker
```

### Важный нюанс для сборки образов в WSL2

Minikube изолирован. Чтобы он мог прочитать локально собранный Docker-образ, перенаправляем Docker-клиент терминала на внутренний Minikube:

```bash
eval $(minikube docker-env)
```

>  эту команду нужно выполнять заново в каждом новом окне терминала, если планируется сборка или пересборка Docker-образов

### Cкриншоты
<img width="1671" height="511" alt="image" src="https://github.com/user-attachments/assets/8f4f9216-d9eb-4a04-b5b6-3a2d8e6ec17e" />


---

## Шаг 3: Создание Docker-образа приложения

Создаём простейший веб-сервер на Python, который считывает имя пода из переменной окружения.

### 3.1. Создание папки проекта

```bash
mkdir my-k8s-app && cd my-k8s-app
```

### 3.2. Создание исходного кода приложения (`app.py`)

Выполняем команду `nano app.py` и вставляем следующий код:

```python
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        # Возвращает имя пода, чтобы мы видели работу балансировщика
        pod_name = os.getenv('POD_NAME', 'Unknown Pod')
        self.wfile.write(f"<h1>Привет из Kubernetes!</h1><p>Привет от пода: {pod_name}</p>".encode())

server = HTTPServer(('0.0.0.0', 8080), MyHandler)
print("Сервер запущен на порту 8080...")
server.serve_forever()
```

### 3.3. Создание спецификации сборки (`Dockerfile`)

Выполняем команду `nano Dockerfile` и вставляем конфигурацию:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
```

### 3.4. Сборка образа

Убеждаемся, что команда `eval $(minikube docker-env)` выполнена, и собираем образ:

```bash
docker build -t my-app:v1 .
```

Проверить, что все хорошо, можно командой `docker images`. В списке должен появиться `my-app:v1`.

### Cкриншоты
<img width="1451" height="299" alt="image" src="https://github.com/user-attachments/assets/e6793f28-5af0-45e1-a661-44ee385555ea" />

---

## Шаг 4: Развертывание Deployment и масштабирование

Создаём единый манифест конфигурации для развертывания подов и обеспечения сетевого доступа.

### 4.1. Создание манифеста (`deployment.yaml`)

Выполняем команду `nano deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  replicas: 3 # Устанавливаем изначальное количество подов на 3 по заданию
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: python-app
        image: my-app:v1
        imagePullPolicy: Never # Строго указывает k8s брать локальный образ Minikube
        ports:
        - containerPort: 8080
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        resources: # Ограничения жизненно необходимы для расчёта метрик HPA!
          requests:
            cpu: "100m"
          limits:
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
    - port: 8080
      targetPort: 8080
      nodePort: 30080
```

### 4.2. Применение конфигурации в кластере

```bash
kubectl apply -f deployment.yaml
```

### 4.3. Проверка статуса компонентов

```bash
kubectl get pods
```

Убеждаемся, что все три пода перешли в состояние `Running`.

### Cкриншоты
<img width="1566" height="208" alt="image" src="https://github.com/user-attachments/assets/c207038e-2237-4f61-8d52-4fcebbdfc16f" />

---

## Шаг 5: Настройка Metrics Server и автомасштабирования (HPA)

Для динамического изменения числа реплик в зависимости от нагрузки кластеру необходим сборщик метрик.

### 5.1. Установка Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

#### Решение проблемы с метриками под WSL/Minikube

Официальный Metrics Server часто блокирует работу из-за самоподписанных TLS-сертификатов Minikube. Для гарантированного исправления активируем адаптированный эддон:

```bash
minikube addons enable metrics-server
```

Спустя 1–2 минуты можно сделать проверку, с помощью  утилиты `kubectl top pods`. Если выводятся данные по подам — всё хорошо. 
### Cкриншоты
<img width="1539" height="228" alt="image" src="https://github.com/user-attachments/assets/5fb3fc65-cd6e-4b44-9492-d8db174dea32" />


### 5.2. Настройка Horizontal Pod Autoscaler (HPA)

Устанавливаем правила: держать лимит использования CPU на уровне 50%, масштабировать поды в диапазоне от 2 до 5 штук:

```bash
kubectl autoscale deployment my-app --cpu-percent=50 --min=2 --max=5
```

### 5.3. Проверка HPA

```bash
kubectl get hpa
```

Спустя пару минут в колонке `TARGETS` значение должно измениться с `<unknown>/50%` на стабильные `0%/50%`.

### Cкриншоты
<img width="1502" height="205" alt="image" src="https://github.com/user-attachments/assets/6b1987c3-0266-4fc0-8ab2-c262d6e796b4" />

---

## Шаг 6: Развертывание мониторинга Prometheus и Grafana

Устанавливаем готовый стек мониторинга с помощью менеджера пакетов Helm.

### 6.1. Подключение официального репозитория

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

### 6.2. Установка стека мониторинга

```bash
helm install prometheus prometheus-community/kube-prometheus-stack
```

Установка занимает 1–2 минуты. Убеждаемся в стабильности запуска всех служебных системных подов командой `kubectl get pods`.

### 6.3. Доступ к Grafana из Windows (Port Forwarding)

Так как WSL не имеет графического интерфейса с браузером, пробрасываем порты из виртуальной сети напрямую на хост-машину Windows.

Выполняем команду в терминале Ubuntu:

```bash
kubectl port-forward svc/prometheus-grafana 3000:80
```

> Оставляем данный терминал открытым — команда должна оставаться запущенной.

### 6.4. Вход в панель управления

Открываем любой браузер внутри основной ОС Windows и переходим по адресу:

- **URL:** http://localhost:3000 (или http://127.0.0.1:3000)
- **Логин:** `admin`
- **Пароль по умолчанию:** `prom-operator`

Если пароль не подходит, в новом окне терминала WSL выполняем декодирование секрета:

```bash
kubectl get secret prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

### 6.5. Импорт интерактивного дашборда

1. В левом меню Grafana переходим в **Dashboards → New → Import**.
2. В поле «Import via grafana.com» указываем ID: `15760` (Kubernetes Views / Global) или `8588` (для отслеживания Workloads).
3. Нажимаем **Load**.
4. В нижней графе **Prometheus** выбираем единственный подключенный Data Source.
5. Нажимаем **Import**.

---

## Шаг 7: Проведение нагрузочного тестирования

Чтобы наглядно зафиксировать пики нагрузки в Grafana и процесс масштабирования подов в консоли, запускаем нагрузочный тест.

### Изолированный запуск нагрузки изнутри кластера (рекомендуется для WSL)

Так как сеть WSL изолирована, запускаем симуляцию запросов из контейнера-соседа. Создаём временный под и проваливаемся в его консоль:

```bash
kubectl run test-load --rm -it --image=busybox -- /bin/sh
```

Внутри открывшейся командной строки контейнера (`/ #`) вводим бесконечный цикл запросов на внутренний CLUSTER-IP сервиса (узнать его можно командой `kubectl get svc`):

```bash
while true; do wget -q -O- http://<ТВОЙ_CLUSTER_IP>:8080; done
```

В параллельных окнах терминала WSL наблюдаем динамику:

- `kubectl get hpa -w` — фиксирует скачок нагрузки процессора (например, `103%/50%`).
- `kubectl get pods -w` — показывает автоматическое создание новых подов вплоть до 5 штук.
- В Grafana на импортированном дашборде отображаются графики пиков CPU и сети.

По окончании теста нажимаем `Ctrl + C` в окне busybox и вводим `exit` — под автоматически удалится. Кластер плавно проведёт демасштабирование (scale down) обратно до изначального уровня.
