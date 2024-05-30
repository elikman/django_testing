import pytest
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from news.forms import CommentForm

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_news_count(client, news_list):
    """Количество новостей на главной странице."""
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    assert object_list is not None, \
        "Ключ 'object_list' не найден в контексте ответа."
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE, \
        f"Ожидалось {settings.NEWS_COUNT_ON_HOME_PAGE} новостей, \
        но получено {news_count}"


def test_news_order(client, news_list):
    """Сортировка новостей от самой свежей к самой старой."""
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    assert object_list is not None, \
        "Ключ 'object_list' не найден в контексте ответа."
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates, \
        "Новости не отсортированы от самой свежей к самой старой."


def test_comments_order(author_client, news_with_comments):
    """Сортировка комментариев в хронологическом порядке."""
    news, comments = news_with_comments
    response = author_client.get(reverse('news:detail', args=(news.id,)))
    assert 'news' in response.context, \
        "Ключ 'news' не найден в контексте ответа."
    news = response.context['news']
    all_comments = news.comment_set.all()
    assert all_comments[0] == comments[0]
    assert all_comments[1] == comments[1]
    assert all_comments[0].created < all_comments[1].created, \
        "Комментарии не отсортированы в хронологическом порядке."


def test_anonymous_client_has_no_form(client, news):
    """Анонимному пользователю недоступна форма для отправки комментария."""
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert 'form' not in response.context, \
        "Анонимному пользователю доступна форма для отправки комментария."


def test_authorized_client_has_comment_form(author_client, news):
    """Авторизованному пользователю доступна форма для отправки комментария."""
    url = reverse('news:detail', args=(news.id,))
    response = author_client.get(url)
    assert 'form' in response.context, \
        "Авторизованному пользователю недоступна форма \
        для отправки комментария."
    form = response.context['form']
    assert isinstance(form, CommentForm), \
        "Форма в контексте не является экземпляром CommentForm."
