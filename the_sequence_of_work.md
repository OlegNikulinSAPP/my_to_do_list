# My To Do List - Django REST API с JWT

Проект для управления задачами с авторизацией и защитой доступа.

---
1. Обновляем `pip`:

```bash
python -m pip install --upgrade pip
```
---
2. Установка Django:

```bash
pip install django
```
---
3. Создаём проект командой:
```bash
django-admin startproject todo_api .
```
---
4. Создаём приложение `tasks`:
```bash
python manage.py startapp tasks
```
---
5. Установка зависимостей:
```bash
pip install djangorestframework djangorestframework-simplejwt python-dotenv
```
---
6. Создать `requirements.txt`:
```bash
pip freeze > requirements.txt
```
---
7. Создать файл `.gitignore` в корне проекта.

Содержимое:
```
# Django
*.log
*.pot
*.pyc
__pycache__/
db.sqlite3
media/
staticfiles/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```
---
8. Создать файл `.env` в корне проекта.

Содержимое:
```env
SECRET_KEY=ваш_секретный_ключ_сгенерируйте_новый
DEBUG=True
```
---
9. Настроить `settings.py` для чтения переменных из `.env`:

+ В начало файла `todo_api/settings.py`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
```
+ Строку с `SECRET_KEY` и заменить на:
```python
SECRET_KEY = os.getenv('SECRET_KEY')
```
+ `DEBUG` заменить на:
```python
DEBUG = os.getenv('DEBUG') == 'True'
```
---
10. Добавить `'rest_framework'`, `'rest_framework_simplejwt'` и `'tasks'` в `INSTALLED_APPS` в `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework_simplejwt',
    'tasks',
]
```
---
11. Добавить настройки REST Framework и JWT в конец `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
```
---

12. Создаем модели `Category` и `Task` (базовый вариант)

Файл: `tasks/models.py`
```python
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)

class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_tasks'
    )
    categories = models.ManyToManyField(Category, blank=True)
```
Примечание.
**`related_name='authored_tasks'`** – имя для обратного доступа от `User` к `Task` через поле `author`.

**Как работает:**
1. Есть `User` (автор) и `Task` (задача с полем `author = ForeignKey(User)`).
2. Без `related_name`: чтобы получить все задачи пользователя, используем `user.task_set.all()`.
3. **С `related_name='authored_tasks'`**: используем `user.authored_tasks.all()`.

**Почему важно:**

При добавлении **ещё одного** поля, например, `responsible`:  
- `author` → `user.authored_tasks.all()` (задачи, где user — автор)
- `responsible` → `user.responsible_tasks.all()` (задачи, где user — ответственный)

**Итог:** Чистое разделение двух разных связей одного пользователя с задачами.

13. Создаем и применяем миграции для моделей:

```bash
python manage.py makemigrations
python manage.py migrate
```

14. Создаем файл `tasks/serializers.py` с содержимым:

```python
from rest_framework import serializers
from .models import Task, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class TaskSerializer(serializers.ModelSerializer):
    # Детали категорий для чтения
    categories = CategorySerializer(many=True, read_only=True)
    
    # Поле для приёма ID категорий при создании/обновлении
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        source='categories',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'deadline',
            'completed', 'created_at', 'author',
            'categories', 'category_ids'
        ]
        read_only_fields = ['author', 'created_at']
```

**Примечание:**
1. `PrimaryKeyRelatedField` принимает список ID и связывает с `ManyToMany` полем
2. `category_ids` только для входящих данных (`write_only=True`), в ответе не показывается
3. В ответе API будет полноценный список объектов категорий в поле `categories`

---

---

# **Краткий итог: как работает TaskSerializer**

## **1. Сериализатор — это «упаковщик/распаковщик»**
- **Задача:** Переводит игрушки (данные) между шкафом (базой данных) и коробкой (JSON-запросом)
- **Как работает:**  
  📦 → 🧸 (распаковка: JSON → Python объект)  
  🧸 → 📦 (упаковка: Python объект → JSON)

---

## **2. Два поля для категорий — ГЛАВНАЯ ХИТРОСТЬ**

### **Поле №1: `categories` (только ПОКАЗЫВАЕТ)**
```python
categories = CategorySerializer(many=True, read_only=True)
```
- **Что делает:** Показывает категории **красиво**, с именами  
  `[{"id": 1, "name": "Работа"}, {"id": 2, "name": "Дом"}]`
- **Особенность:** `read_only=True` → клиент **не может** сюда писать
- **Аналогия:** Витрина магазина — можно смотреть, нельзя трогать

### **Поле №2: `category_ids` (только ПРИНИМАЕТ)**
```python
category_ids = PrimaryKeyRelatedField(... write_only=True)
```
- **Что делает:** Принимает от клиента **просто список цифр**  
  `[1, 2]`
- **Особенность:** `write_only=True` → в ответах **не показывается**
- **Магия `source='categories'`:** Полученные цифры [1, 2] превращает в реальные категории и записывает в БД
- **Аналогия:** Щель для писем — можно бросать, нельзя доставать

---

## **3. Клиент должен ЗНАТЬ ID категорий**
- Клиент **сначала** спрашивает: «Какие есть категории?» (`GET /api/categories/`)
- Получает ответ: `[{"id": 1, "name": "Работа"}, {"id": 2, "name": "Дом"}]`
- **Теперь знает:** Работа = ID 1, Дом = ID 2
- Создаёт задачу: `{"title": "Уборка", "category_ids": [2]}`

---

## **4. В БД хранятся только СВЯЗИ (ID → ID)**
```
Задача "Уборка" (id=5) → Связана с категорией "Дом" (id=2)
```
Таблица связей:
```
task_id | category_id
--------|------------
   5    |     2
```

---

## **5. Полный цикл на примере:**

```
1. Клиент → Сервер (POST):
   {"title": "Купить молоко", "category_ids": [1, 3]}

2. Сервер находит в БД:
   - Категорию id=1 ("Продукты")
   - Категорию id=3 ("Срочно")

3. Сервер сохраняет в БД:
   - Запись о задаче
   - Две связи: задача → категория 1, задача → категория 3

4. Клиент ← Сервер (GET):
   {
     "id": 10,
     "title": "Купить молоко",
     "categories": [  ← красиво!
       {"id": 1, "name": "Продукты"},
       {"id": 3, "name": "Срочно"}
     ]
   }
```

---

## **Что ты отлично понял:**
✅ **Асимметрия полей** — одно для ввода, другое для вывода  
✅ **`read_only` vs `write_only`** — разделение ответственности  
✅ **`source='categories'`** — мост между API-именем и именем в модели  
✅ **Клиент управляет ID** — должен сам знать соответствие ID ↔ название  
✅ **ManyToMany в БД** — хранится как таблица связей  

## **Простая аналогия:**
У тебя есть **альбом с наклейками** (категории), у каждой наклейки есть **номер** (ID).

- Ты говоришь другу: «Наклей наклейки №1 и №3» (`category_ids: [1, 3]`)
- Друг наклеивает их на страницу (устанавливает связи в БД)
- Потом показывает страницу: «Смотри, вот наклейка "Солнце" (id=1), вот "Луна" (id=3)» (`categories`)

**Ты не говоришь:** «Наклей наклейку "Солнце"» (с названием)  
**Ты говоришь:** «Наклей наклейку №1» (с номером)  
Но когда смотришь результат — видишь и номера, и названия.

---

---

15. Создаем `tasks/views.py` с ViewSet:

```python
from rest_framework import viewsets, permissions
from .models import Task, Category
from .serializers import TaskSerializer, CategorySerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(author=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Category.objects.all()
```
Примечание:

**`get_queryset`** – вызывается автоматически при любом запросе списка (`GET /tasks/`) или деталей (`GET /tasks/1/`). Фильтрует задачи только текущего пользователя.

**`perform_create`** – вызывается автоматически при создании задачи (`POST /tasks/`). Устанавливает `author=self.request.user` перед сохранением.

**Пример:**
- `GET /tasks/` → Django REST → `get_queryset()` → возвращает `Task.objects.filter(author=request.user)`
- `POST /tasks/` → Django REST → `perform_create(serializer)` → вызывает `serializer.save(author=request.user)`

**Следующий шаг:** Настроить роутеры и URL в `tasks/urls.py`:

16. Создаем файл `tasks/urls.py`:
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
```

17. Подключаем в основном `todo_api/urls.py`:
```python
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('tasks.urls')),
]
```

18. Создаем суперпользователя и запустить сервер:

```bash
python manage.py createsuperuser
python manage.py runserver
```

**Проверка:**
1. http://127.0.0.1:8000/api/token/ (POST для получения JWT)
2. http://127.0.0.1:8000/api/tasks/ (с заголовком `Authorization: Bearer <ваш_token>`)
3. http://127.0.0.1:8000/admin/ (вход для суперпользователя)

**Нет, токен не вечный.** Используются настройки по умолчанию `django-rest-framework-simplejwt`:

- **Access токен:** 5 минут жизни
- **Refresh токен:** 1 день жизни

**Настроить время жизни** можно в `settings.py`:
```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}
```

**Как работает:**
1. Access токен истекает через 5 мин → использовать refresh токен для получения нового
2. Refresh токен истекает через 1 день → нужно заново логиниться (`/api/token/`)

**Следующий шаг:** Тестирование API.

**Шаг: Установка и использование HTTPie для тестирования API**

1. **Установите HTTPie:**
   ```bash
   pip install httpie
   ```

2. **Получение JWT токена:**
   ```bash
   http POST http://127.0.0.1:8000/api/token/ username=ваш_логин password=ваш_пароль
   ```

3. **Создание задачи (скопируйте access токен из предыдущего ответа):**
   ```bash
   http POST http://127.0.0.1:8000/api/tasks/ \
     "Authorization:Bearer ваш_access_токен" \
     title="Первая задача" \
     description="Тест API"
   ```

4. **Получение списка задач:**
   ```bash
   http GET http://127.0.0.1:8000/api/tasks/ "Authorization:Bearer ваш_access_токен"
   ```

5. **Обновление токена (используйте refresh токен из первого ответа):**
   ```bash
   http POST http://127.0.0.1:8000/api/token/refresh/ refresh=ваш_refresh_токен
   ```