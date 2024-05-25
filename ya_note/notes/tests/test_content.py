from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()
URL_NOTE_LIST: str = reverse('notes:list')
CONTEXT_OBJECT_LIST: str = 'object_list'


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.notes = Note.objects.create(
            title='slug',
            text='Текст',
            slug='note-slug',
            author=cls.author
        )

    def test_notes_list_for_authors(self):
        self.client.force_login(self.author)
        response = self.client.get(URL_NOTE_LIST)
        object_list = response.context.get(CONTEXT_OBJECT_LIST)
        self.assertIsNotNone(object_list)
        self.assertTrue((self.notes in object_list))

    def test_notes_list_for_other_users(self):
        self.client.force_login(self.reader)
        response = self.client.get(URL_NOTE_LIST)
        object_list = response.context.get(CONTEXT_OBJECT_LIST)
        self.assertIsNotNone(object_list)
        self.assertFalse((self.notes in object_list))

    def test_pages_contains_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.notes.slug,)),
        )
        self.client.force_login(self.author)
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIsInstance(response.context['form'], NoteForm)
