import pytest

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.conf import settings

from news.models import News, Comment


User = get_user_model()


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


@pytest.fixture
def news_with_comments(author_client):
    author = User.objects.create(username='Комментатор')
    news = News.objects.create(
        title='Тестовая новость', text='Просто текст.'
    )
    now = timezone.now()
    comments = []
    for index in range(2):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
        comments.append(comment)
    return news, comments
