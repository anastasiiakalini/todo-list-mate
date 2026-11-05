from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    content = models.CharField(max_length=250)
    datetime = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    is_done = models.BooleanField(default=False)

    tags = models.ManyToManyField(
        Tag,
        related_name="tasks",
        blank=True,
    )

    class Meta:
        ordering = ["is_done", "-datetime"]

    def __str__(self):
        return self.content
