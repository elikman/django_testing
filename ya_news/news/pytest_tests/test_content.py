import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from news.models import News, Comment
from news.forms import CommentForm

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_news_count(client, news_list):
    """Количество новостей на главной странице."""
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    if object_list is not None:
        news_count = len(object_list)
        assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE
    else:
        raise ValueError("Ключ 'object_list' не найден в контексте ответа.")


def test_news_order(client, news_list):
    """Сортировка новостей от самой свежей к самой старой."""
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    if object_list is not None:
        all_dates = [news.date for news in object_list]
        sorted_dates = sorted(all_dates, reverse=True)
        assert all_dates == sorted_dates
    else:
        raise ValueError("Ключ 'object_list' не найден в контексте ответа.")


def test_comments_order(author_client):
    """Сортировка комментариев в хронологическом порядке."""
    author = User.objects.create(username='Комментатор')
    news = News.objects.create(
        title='Тестовая новость', text='Просто текст.'
    )
    now = timezone.now()
    for index in range(2):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
    response = author_client.get(reverse('news:detail', args=(news.id,)))
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    assert all_comments[0].created < all_comments[1].created


def test_anonymous_client_has_no_form(client, news):
    """Анонимному пользователю недоступна форма для отправки комментария."""
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert 'form' not in response.context


def test_authorized_client_has_comment_form(author_client, news):
    """Авторизованному пользователю доступна форма для отправки комментария."""
    url = reverse('news:detail', args=(news.id,))
    response = author_client.get(url)
    assert 'form' in response.context
    form = response.context['form']
    assert isinstance(form, CommentForm)
