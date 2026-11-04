from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tasks.models import (
    Tag,
    Task
)


class TaskModelTests(TestCase):
    def test_new_task_is_not_done_and_has_no_deadline(self):
        task = Task.objects.create(content="Learn Django")

        self.assertFalse(task.is_done)
        self.assertIsNone(task.deadline)
        self.assertIsNotNone(task.datetime)

    def test_task_can_have_multiple_tags(self):
        task = Task.objects.create(content="Finish exercises")
        study = Tag.objects.create(name="Study")
        python = Tag.objects.create(name="Python")

        task.tags.add(study, python)

        self.assertEqual(task.tags.count(), 2)
        self.assertIn(task, study.tasks.all())
        self.assertIn(task, python.tasks.all())

    def test_tasks_are_ordered_by_status_then_newest_first(self):
        now = timezone.now()
        old_pending = Task.objects.create(content="Old pending")
        new_pending = Task.objects.create(content="New pending")
        old_done = Task.objects.create(content="Old done", is_done=True)
        new_done = Task.objects.create(content="New done", is_done=True)

        Task.objects.filter(pk=old_pending.pk).update(datetime=now - timedelta(days=3))
        Task.objects.filter(pk=new_pending.pk).update(datetime=now - timedelta(days=1))
        Task.objects.filter(pk=old_done.pk).update(datetime=now - timedelta(days=4))
        Task.objects.filter(pk=new_done.pk).update(datetime=now)

        self.assertEqual(
            list(Task.objects.values_list("content", flat=True)),
            ["New pending", "Old pending", "New done", "Old done"],
        )


class TaskViewTests(TestCase):
    def test_home_page_and_sidebar(self):
        self.assertEqual(reverse("tasks:task-list"), "/")

        response = self.client.get(reverse("tasks:task-list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_list.html")
        self.assertContains(response, "Home")
        self.assertContains(response, "Tags")
        self.assertContains(response, "Add task")

    def test_home_displays_task_information(self):
        tag = Tag.objects.create(name="Work")
        task = Task.objects.create(
            content="Prepare a report",
            deadline=timezone.now() + timedelta(days=2),
        )
        task.tags.add(tag)

        response = self.client.get(reverse("tasks:task-list"))

        self.assertContains(response, "Prepare a report")
        self.assertContains(response, "Not done")
        self.assertContains(response, "Created:")
        self.assertContains(response, "Tags:")
        self.assertContains(response, "Work")
        self.assertContains(response, "text-burgundy")

    def test_create_task_without_optional_fields(self):
        response = self.client.post(
            reverse("tasks:task-create"),
            {"content": "Buy groceries", "deadline": ""},
        )

        self.assertRedirects(response, reverse("tasks:task-list"))
        task = Task.objects.get(content="Buy groceries")
        self.assertFalse(task.is_done)
        self.assertIsNone(task.deadline)
        self.assertEqual(task.tags.count(), 0)

    def test_create_task_with_deadline_and_multiple_tags(self):
        work = Tag.objects.create(name="Work")
        urgent = Tag.objects.create(name="Urgent")

        response = self.client.post(
            reverse("tasks:task-create"),
            {
                "content": "Submit application",
                "deadline": "2026-12-10T18:30",
                "tags": [str(work.pk), str(urgent.pk)],
            },
        )

        self.assertRedirects(response, reverse("tasks:task-list"))
        task = Task.objects.get(content="Submit application")
        self.assertIsNotNone(task.deadline)
        self.assertEqual(task.tags.count(), 2)

    def test_update_task(self):
        task = Task.objects.create(content="Old task")
        tag = Tag.objects.create(name="Personal")

        response = self.client.post(
            reverse("tasks:task-update", args=[task.pk]),
            {
                "content": "Updated task",
                "deadline": "",
                "tags": [str(tag.pk)],
                "is_done": "on",
            },
        )

        self.assertRedirects(response, reverse("tasks:task-list"))
        task.refresh_from_db()
        self.assertEqual(task.content, "Updated task")
        self.assertTrue(task.is_done)
        self.assertIn(tag, task.tags.all())

    def test_delete_task(self):
        task = Task.objects.create(content="Remove me")
        url = reverse("tasks:task-delete", args=[task.pk])

        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url)

        self.assertRedirects(response, reverse("tasks:task-list"))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_complete_and_undo_task(self):
        task = Task.objects.create(content="Read a book")
        url = reverse("tasks:task-toggle", args=[task.pk])

        response = self.client.post(url)
        self.assertRedirects(response, reverse("tasks:task-list"))
        task.refresh_from_db()
        self.assertTrue(task.is_done)

        response = self.client.post(url)
        self.assertRedirects(response, reverse("tasks:task-list"))
        task.refresh_from_db()
        self.assertFalse(task.is_done)

    def test_toggle_does_not_allow_get(self):
        task = Task.objects.create(content="Keep status")
        url = reverse("tasks:task-toggle", args=[task.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        task.refresh_from_db()
        self.assertFalse(task.is_done)


class TagViewTests(TestCase):
    def test_tag_list_page(self):
        Tag.objects.create(name="Sport")
        self.assertEqual(reverse("tasks:tag-list"), "/tags/")

        response = self.client.get(reverse("tasks:tag-list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/tag_list.html")
        self.assertContains(response, "Sport")
        self.assertContains(response, "Update")
        self.assertContains(response, "Delete")

    def test_create_tag(self):
        response = self.client.post(
            reverse("tasks:tag-create"), {"name": "Study"}
        )

        self.assertRedirects(response, reverse("tasks:tag-list"))
        self.assertTrue(Tag.objects.filter(name="Study").exists())

    def test_update_tag(self):
        tag = Tag.objects.create(name="Old name")
        response = self.client.post(
            reverse("tasks:tag-update", args=[tag.pk]),
            {"name": "New name"},
        )

        self.assertRedirects(response, reverse("tasks:tag-list"))
        tag.refresh_from_db()
        self.assertEqual(tag.name, "New name")

    def test_delete_tag(self):
        tag = Tag.objects.create(name="Remove me")
        url = reverse("tasks:tag-delete", args=[tag.pk])

        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url)

        self.assertRedirects(response, reverse("tasks:tag-list"))
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())

