## Технології

* Python 3.14, Django, Django REST Framework
* JWT автентифікація (djangorestframework-simplejwt)
* Celery + Redis — фонова синхронізація товарів і курсів валют
* pytest — тести
* Зовнішні API: dummyjson.com/products, fakestoreapi.com/products, НБУ (курси валют)

## Налаштування і запуск проекту:

`python -m venv .venv`

`source .venv/bin/activate`  

Windows: `.venv\Scripts\activate`

`pip install -r requirements.txt`

`python manage.py migrate`

`python manage.py createsuperuser`

`python manage.py runserver`

## Ендпоінти API

### Автентифікація (users)

Реєстрація й логін реалізовані через email+пароль, JWT токени.

### Каталог товарів (catalog)

Публічні ендпоінти — доступні без автентифікації. Усюди можна вказати параметр currency (за замовчуванням — UAH), курс береться з останнього доступного курсу НБУ.

### Підписки на зниження ціни (alerts)

Потребують автентифікації. Користувач бачить і керує лише власними підписками.

### Курси валют НБУ (currency)

Курси валют НБУ (поточні та історичні), конвертація цін між валютами. Власних ендпоінтів немає — використовується іншими застосунками.
