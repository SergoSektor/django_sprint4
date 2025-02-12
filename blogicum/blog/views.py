from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    CreateView, DetailView, ListView, UpdateView
)
from django.utils import timezone
from django.urls import reverse

from .models import Post, Category, Comment
from .forms import PostForm, UserProfileForm, CommentForm

User = get_user_model()
MAX_POSTS = settings.MAX_POSTS


def get_optimized_post_queryset(manager=Post.objects,
                                apply_filters=True,
                                apply_annotation=True,
                                user=None):
    queryset = manager.select_related('author', 'category', 'location')

    if apply_filters:
        if user is not None:
            # Автор видит свои посты, даже если категория снята с публикации
            queryset = queryset.filter(
                (Q(is_published=True) | Q(author=user)) & Q(
                    (Q(category__is_published=True) | Q(author=user)),
                    pub_date__lte=timezone.now()
                ))
        else:
            queryset = queryset.filter(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            )

    if apply_annotation:
        queryset = queryset.annotate(
            comment_count=Count('comments')).order_by('-pub_date')

    return queryset


class OnlyAuthorMixin(UserPassesTestMixin):
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author


class IndexView(ListView):
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = MAX_POSTS

    def get_queryset(self):
        return get_optimized_post_queryset(
            apply_filters=True,
            apply_annotation=True
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        user = (
            self.request.user if self.request.user.is_authenticated else None
        )
        return get_optimized_post_queryset(
            apply_filters=True,
            apply_annotation=True,
            user=user  # Передаем пользователя только если он авторизован
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.get_object().comments.select_related(
            'author').all()
        return context


class CategoryPostView(ListView):
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = MAX_POSTS

    def get_queryset(self):
        category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'])
        return get_optimized_post_queryset(manager=category.posts,
                                           apply_filters=True,
                                           apply_annotation=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        context['category'] = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user})


class PostUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        post_id = self.kwargs.get('post_id')
        return redirect('blog:post_detail', post_id)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.object.id}
        )


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Проверяем, что пользователь является автором поста
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostForm(instance=post)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', request.user.username)

    return render(request, 'blog/create.html', context={'form': form})


class ProfileView(ListView):
    template_name = 'blog/profile.html'
    context_object_name = 'post_list'
    paginate_by = MAX_POSTS

    def get_queryset(self):
        username = self.kwargs.get('username')
        user = get_object_or_404(User, username=username)
        if self.request.user == user:
            # Автор видит все свои посты, включая снятые с публикации
            return Post.objects.filter(author=user).annotate(
                comment_count=Count('comments')
            ).order_by('-pub_date')
        else:
            # Другие пользователи видят только опубликованные посты
            return get_optimized_post_queryset(
                manager=Post.objects.filter(author=user),
                apply_filters=True,
                apply_annotation=True
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get('username')
        context['profile'] = get_object_or_404(User, username=username)
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_object(self, queryset=None):

        post_id = self.kwargs.get('post_id')
        comment_id = self.kwargs.get('comment_id')

        comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

        return comment

    def get_success_url(self):
        comment = self.get_object()
        return reverse('blog:post_detail',
                       kwargs={'post_id': comment.post.id})


@login_required
def comment_delete(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/comment.html', {
        'post': comment.post,
        'comment': comment,
    })
