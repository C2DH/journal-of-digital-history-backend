from django import forms
from jdhapi.models import Article
from jdhapi.utils.gitup_repository import is_socialmediacover_exist


class ArticleForm(forms.ModelForm):
    def clean(self):
        doi = self.cleaned_data['doi']
        status = self.cleaned_data['status']
        repository_url = self.cleaned_data['repository_url']
        if status == Article.Status.PUBLISHED:
            if not doi:
                raise forms.ValidationError({'doi': "Doi is mandatory if published"})
            if not is_socialmediacover_exist(repository_url):
                raise forms.ValidationError({'repository_url': "No social media cover uploaded in the GitHub repository"})

