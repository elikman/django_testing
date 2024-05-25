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
        url = reverse('notes:add')
        self.client.force_login(self.author)
        notes_before = Note.objects.count()
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_CREATE_DELETE)
        new_note = Note.objects.last()
        compare = (
            (new_note.title, self.form_data['title']),
            (new_note.text, self.form_data['text']),
            (new_note.slug, self.form_data['slug']),
            (new_note.author, self.author),
        )
        for new_data, old_data in compare:
            with self.subTest():
                self.assertEqual(new_data, old_data)

    def test_anonymous_user_cant_create_note(self):
        url = reverse('notes:add')
        notes_before = Note.objects.count()
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        redirect_url = f'{login_url}?next={url}'
        self.assertRedirects(response, redirect_url)
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_EDIT)

    def test_not_unique_slug(self):
        url = reverse('notes:add')
        self.form_data['slug'] = self.notes.slug
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.notes.slug + WARNING)
        )

    def test_empty_slug(self):
        url = reverse('notes:add')
        self.form_data.pop('slug')
        self.client.force_login(self.author)
        notes_before = Note.objects.count()
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_CREATE_DELETE)
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        url = reverse('notes:edit', args=(self.notes.slug,))
        self.client.force_login(self.author)
        notes_before = Note.objects.count()
        response = self.client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_EDIT)
        self.notes.refresh_from_db()
        compare = (
            (self.notes.title, self.form_data['title']),
            (self.notes.text, self.form_data['text']),
            (self.notes.slug, self.form_data['slug']),
        )
        for new_data, old_data in compare:
            with self.subTest():
                self.assertEqual(new_data, old_data)

    def test_other_user_cant_edit_note(self):
        url = reverse('notes:edit', args=(self.notes.slug,))
        self.client.force_login(self.reader)
        response = self.client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.notes.id)
        compare = (
            (self.notes.title, note_from_db.title),
            (self.notes.text, note_from_db.text),
            (self.notes.slug, note_from_db.slug),
        )
        for new_data, old_data in compare:
            with self.subTest():
                self.assertEqual(new_data, old_data)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.notes.slug,))
        self.client.force_login(self.author)
        notes_before = Note.objects.count()
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        notes_after = Note.objects.count()
        self.assertEqual((notes_before - notes_after), DIFF_CREATE_DELETE)

    def test_other_user_cant_delete_note(self):
        url = reverse('notes:delete', args=(self.notes.slug,))
        self.client.force_login(self.reader)
        notes_before = Note.objects.count()
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_after = Note.objects.count()
        self.assertEqual((notes_after - notes_before), DIFF_EDIT)
