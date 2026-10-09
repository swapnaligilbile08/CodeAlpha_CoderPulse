from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('category', 'title', 'body', 'image')
        widgets = {'body': forms.Textarea(attrs={'rows': 5})}
