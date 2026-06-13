# Лаба 7. Развертыване веб-сервиса в Kubernetes (Minikube) с мониторингом и автоскейлингом
Выполнили
Дьячкова Алла, 367206
Олейник Полина, 409270
Рудникова Виктория, 367518

Задачи:

1) развернуть minicube 

2) создать docker образ вашего приложения;

3) создать deployment;

4) установить кол-во подов на 3

5) добавьте Metrics Server (`kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`).

6) настройте Horizontal Pod Autoscaler (HPA), чтобы масштабировать поды при увеличении нагрузки (`kubectl autoscale deployment my-app --cpu-percent=50 --min=2 --max=5`).

7) настройте Prometheus и Grafana через (`helm install prometheus prometheus-community/kube-prometheus-stack`). Настройте дашборды в Grafana для мониторинга нагрузки (хотя бы один)


# Ссылка на видео-демонстрацию
https://drive.google.com/file/d/1XC42x6UZD7oZnz3bEVZ2IiPxdfzNgmDY/view?usp=sharing


# Инструкция

> *работа выполнялась в окружении WSL2*


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

Выполняем команду `nano app.py` и вставляем код (см. файл `app.py`)

### 3.3. Создание спецификации сборки (`Dockerfile`)

Выполняем команду `nano Dockerfile` и вставляем конфигурацию (см. файл `Dockerfile`)

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

Выполняем команду `nano deployment.yaml` и пишем манифест (см. файл `deployment.yaml`)


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

Спустя пару минут в колонке `TARGETS` значение должно измениться с `<unknown>/50%` на `1%/50%`.

### Cкриншоты
<img width="1502" height="205" alt="image" src="https://github.com/user-attachments/assets/6b1987c3-0266-4fc0-8ab2-c262d6e796b4" />
<img width="1554" height="71" alt="image" src="https://github.com/user-attachments/assets/44097c8e-2fea-47e6-97ba-88012ac112f2" />

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

Убеждаемся в стабильности запуска всех служебных системных подов с помощью команды `kubectl get pods`.


### 6.3. Доступ к Grafana из Windows (Port Forwarding)

Так как WSL не имеет графического интерфейса с браузером, пробрасываем порты из виртуальной сети напрямую на хост-машину Windows.

Выполняем команду в терминале Ubuntu:

```bash
kubectl port-forward svc/prometheus-grafana 3000:80
```

> Оставляем данный терминал открытым — команда должна оставаться запущенной.

### 6.4. Вход в панель управления

Открываем браузер внутри основной ОС Windows и переходим по адресу:

- **URL:** http://localhost:3000 (или http://127.0.0.1:3000)
- **Логин:** `admin`
- **Пароль:** чтобы найти пароль, в новом окне терминала WSL пишем:

```bash
kubectl get secret prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

### 6.5. Добавление дашборда

В Grafana можно импортировать дашборт по ID. Для этого в левом меню  переходим в **Dashboards → New → Import**. В поле «Import via grafana.com» указываем ID: `15760` (Kubernetes Views / Global) или `8588` (для отслеживания Workloads).

### Cкриншоты
<img width="1406" height="754" alt="image" src="https://github.com/user-attachments/assets/6381e85c-94b3-4dbb-a3b5-c42b2911f743" />
<img width="1407" height="732" alt="image" src="https://github.com/user-attachments/assets/bd621bdc-9a8f-4297-a412-aaf2090e492d" />

---

## Шаг 7: Проведение нагрузочного тестирования

### Изолированный запуск нагрузки изнутри кластера (рекомендуется для WSL)

Так как сеть WSL изолирована, запускаем симуляцию запросов из контейнера-соседа. Создаём временный под и попадаем в его консоль:

```bash
kubectl run test-load --rm -it --image=busybox -- /bin/sh
```

Внутри открывшейся командной строки контейнера (`/ #`) вводим бесконечный цикл запросов на внутренний CLUSTER-IP сервиса (узнать его можно командой `kubectl get svc`):

```bash
while true; do wget -q -O- http://<CLUSTER_IP>:8080; done
```

В параллельных окнах терминала WSL можно выполнить следующие команды, чтобы посмотреть, что происходит с подами:

- `kubectl get hpa -w` — фиксирует скачок нагрузки процессора (например, `103%/50%`).
- `kubectl get pods -w` — показывает автоматическое создание новых подов.

По окончании теста нажимаем `Ctrl + C`. Кластер плавно проведёт демасштабирование.

### Cкриншоты

`увеличение нагрузки`

<img width="1411" height="316" alt="image" src="https://github.com/user-attachments/assets/2742c8cf-44a3-48fb-a03b-e6a101651042" />
<img width="1455" height="558" alt="image" src="https://github.com/user-attachments/assets/8bd77c3a-3aee-4185-a7b1-6ddd77aa08b8" />

`снижение нагрузки`

<img width="1485" height="229" alt="image" src="https://github.com/user-attachments/assets/bfdb9da9-8024-44c3-827b-7d6899734cec" />
<img width="1514" height="264" alt="image" src="https://github.com/user-attachments/assets/5c8a3b9a-5def-4626-ae54-ff4efae31f65" />



