import pytest
from news.models import News


@pytest.mark.django_db
class TestNews:
    TITLE = 'Заголовок новости'
    TEXT = 'Тестовый текст'

    @pytest.fixture(autouse=True)
    def setup_news(self, db):
        self.news = News.objects.create(
            title=self.TITLE,
            text=self.TEXT,
        )

    def test_successful_creation(self):
        news_count = News.objects.count()
        assert news_count == 1

    def test_title(self):
        assert self.news.title == self.TITLE
