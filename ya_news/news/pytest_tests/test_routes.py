import pytest
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse

from news.models import Comment, News

User = get_user_model()


@pytest.mark.django_db
class TestRoutes:

    @pytest.fixture
    def news(self):
        return News.objects.create(title='Заголовок', text='Текст')

    @pytest.fixture
    def author(self):
        return User.objects.create(username='Лев Толстой')

    @pytest.fixture
    def reader(self):
        return User.objects.create(username='Читатель простой')

    @pytest.fixture
    def comment(self, news, author):
        return Comment.objects.create(
            news=news,
            author=author,
            text='Текст комментария'
        )

    @pytest.fixture
    def urls(self):
        return [
            ('news:home', None),
            ('news:detail', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        ]

    def test_pages_availability(self, client, urls, news):
        for name, args in urls:
            if name == 'news:detail':
                args = (news.id,)
            url = reverse(name, args=args)
            response = client.get(url)
            assert response.status_code == HTTPStatus.OK

    def test_availability_for_comment_edit_and_delete(self, client, author,
                                                      reader, comment):
        users_statuses = [
            (author, HTTPStatus.OK),
            (reader, HTTPStatus.NOT_FOUND),
        ]
        for user, status in users_statuses:
            client.force_login(user)
            for name in ('news:edit', 'news:delete'):
                url = reverse(name, args=(comment.id,))
                response = client.get(url)
                assert response.status_code == status

    def test_redirect_for_anonymous_client(self, client, comment):
        login_url = reverse('users:login')
        for name in ('news:edit', 'news:delete'):
            url = reverse(name, args=(comment.id,))
            redirect_url = f'{login_url}?next={url}'
            response = client.get(url)
            assert response.status_code == HTTPStatus.FOUND
            assert response.url == redirect_url
