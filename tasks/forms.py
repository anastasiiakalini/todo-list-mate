from django import forms
from tasks.models import Tag, Task


class TaskCreationForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Task
        widgets = {
            "deadline": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }
        fields = (
            "content",
            "tags",
            "deadline",
            "is_done",
        )


class TaskInformationUpdateForm(forms.ModelForm):

    class Meta:
        model = Task
        widgets = {
            "deadline": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }
        fields = [
            "content",
            "tags",
            "deadline",
            "is_done",
        ]


class TagCreationForm(forms.ModelForm):

    class Meta:
        model = Tag
        fields = ("name",)


class TagInformationUpdateForm(forms.ModelForm):

    class Meta:
        model = Tag
        fields = ["name"]
