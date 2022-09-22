from django import forms
from jdhapi.models import Article
from jdhapi.utils.gitup_repository import is_socialmediacover_exist


class ArticleForm(forms.ModelForm):
    def clean(self):
        doi = self.cleaned_data['doi']
        status = self.cleaned_data['status']
        repository_url = self.cleaned_data['repository_url']
        notebook_url = self.cleaned_data['notebook_url']
        notebook_path = self.cleaned_data['notebook_path']
        binder_url = self.cleaned_data['binder_url']
        notebook_ipython_url = self.cleaned_data['notebook_ipython_url']
        if status == Article.Status.PUBLISHED:
            if not doi:
                raise forms.ValidationError({'doi': "Doi is mandatory if published"})
            if not is_socialmediacover_exist(repository_url):
                raise forms.ValidationError({'repository_url': "No social media cover uploaded in the GitHub repository"})
        if status == Article.Status.PEER_REVIEW:
            if not repository_url:
                raise forms.ValidationError({'repository_url': "Repository_url is mandatory if published"})
            if not notebook_url:
                raise forms.ValidationError({'notebook_url': "Notebook_url is mandatory if published"})
            if not notebook_path:
                raise forms.ValidationError({'notebook_path': "Notebook_url is mandatory if published"})


