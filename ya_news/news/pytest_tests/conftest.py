import pytest

from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from news.models import News, Comment


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def news():
    return News.objects.create(
        title='Заголовок',
        text='Текст',
    )


@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        news=news,
        text='Комментарий',
        author=author
    )


@pytest.fixture
def form_data():
    return {'text': 'Новый текст'}


@pytest.fixture
def news_list(db):
    today = timezone.now()
    all_news = [
        News(
            title=f'Новость {index}',
            text='Текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)
    return all_news
