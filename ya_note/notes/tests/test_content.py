from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()

DIFF_CREATE_DELETE: int = 1
DIFF_EDIT: int = 0

ADD_URL = reverse('notes:add')
EDIT_URL = reverse('notes:edit', args=('note-slug',))
DELETE_URL = reverse('notes:delete', args=('note-slug',))
SUCCESS_URL = reverse('notes:success')
LOGIN_URL = reverse('users:login')


def compare_objects(obj1, obj2, fields):
    for field in fields:
        with TestCase().subTest(field=field):
            value1 = getattr(obj1, field)
            value2 = getattr(obj2, field)
            TestCase().assertEqual(value1, value2)


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='note-slug',
            author=cls.author
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }

    def test_user_can_create_note(self):
        self.client.force_login(self.author)
        notes_before = Note.objects.count()
        response = self.client.post(ADD_URL, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_CREATE_DELETE)
        new_note = Note.objects.last()
        compare_objects(new_note, Note(
            title=self.form_data['title'],
            text=self.form_data['text'],
            slug=self.form_data['slug'],
            author=self.author
        ), ['title', 'text', 'slug', 'author'])

    def test_anonymous_user_cant_create_note(self):
        notes_before = Note.objects.count()
        response = self.client.post(ADD_URL, data=self.form_data)
        redirect_url = f'{LOGIN_URL}?next={ADD_URL}'
        self.assertRedirects(response, redirect_url)
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_EDIT)

    def test_not_unique_slug(self):
        self.form_data['slug'] = self.notes.slug
        self.client.force_login(self.author)
        response = self.client.post(ADD_URL, data=self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.notes.slug + WARNING)
        )

    def test_empty_slug(self):
        self.form_data.pop('slug')
        self.client.force_login(self.author)
        notes_before = Note.objects.count()
        response = self.client.post(ADD_URL, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_CREATE_DELETE)
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        self.client.force_login(self.author)
        notes_before = Note.objects.count()
        response = self.client.post(EDIT_URL, self.form_data)
        self.assertRedirects(response, SUCCESS_URL)
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_EDIT)
        self.notes.refresh_from_db()
        compare_objects(self.notes, Note(
            title=self.form_data['title'],
            text=self.form_data['text'],
            slug=self.form_data['slug']
        ), ['title', 'text', 'slug'])

    def test_other_user_cant_edit_note(self):
        self.client.force_login(self.reader)
        response = self.client.post(EDIT_URL, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.notes.id)
        compare_objects(self.notes, note_from_db, ['title', 'text', 'slug'])

    def test_author_can_delete_note(self):
        self.client.force_login(self.author)
        notes_before = Note.objects.count()
        response = self.client.post(DELETE_URL)
        self.assertRedirects(response, SUCCESS_URL)
        notes_after = Note.objects.count()
        self.assertEqual((notes_before - notes_after), DIFF_CREATE_DELETE)
        with self.assertRaises(Note.DoesNotExist):
            Note.objects.get(id=self.notes.id)

    def test_other_user_cant_delete_note(self):
        self.client.force_login(self.reader)
        notes_before = Note.objects.count()
        response = self.client.post(DELETE_URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_EDIT)
        note_from_db = Note.objects.get(id=self.notes.id)
        compare_objects(self.notes, note_from_db, ['title', 'text', 'slug'])
