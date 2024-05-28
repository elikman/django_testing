import pytest
from http import HTTPStatus

from pytest_django.asserts import assertRedirects
from django.urls import reverse


@pytest.mark.parametrize(
    'name',
    ('news:home', 'users:login', 'users:logout', 'users:signup')
)
@pytest.mark.django_db
def test_pages_availability_for_anonymous_user(client, name):
    """Страницы доступны анонимным пользователям."""
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_pages_availability_for_author(author_client, news):
    """Страница отдельной новости доступна анонимному пользователю."""
    url = reverse('news:detail', args=(news.id,))
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
@pytest.mark.django_db
def test_pages_availability_for_different_users(
        parametrized_client, name, comment, expected_status
):
    """Доступность редакт-ия/удаления комментария разными пользователями."""
    url = reverse(name, args=(comment.id,))
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_redirect_for_delete_comments(client, comment):
    """Редирект удаления комментария для анонимных пользователей."""
    login_url = reverse('users:login')
    url = reverse('news:delete', args=(comment.id,))
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)


@pytest.mark.django_db
def test_redirect_for_edit_comments(client, comment):
    """Редирект изменения комментария для анонимных пользователей."""
    login_url = reverse('users:login')
    url = reverse('news:edit', args=(comment.id,))
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
