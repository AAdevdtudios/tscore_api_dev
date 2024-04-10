from django import forms
from ckeditor.widgets import CKEditorWidget
from ckeditor.fields import RichTextFormField


class NotificationForm(forms.Form):
    # _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    title = forms.CharField(
        max_length=100,
    )
    description = forms.CharField()
    content = RichTextFormField()
